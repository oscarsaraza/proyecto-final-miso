# S3 Bucket privado para los estáticos del portal Angular
resource "aws_s3_bucket" "web" {
  bucket        = "${var.project_name}-web-portal-${var.environment}"
  force_destroy = true

  tags = {
    Name = "${var.project_name}-web-portal-${var.environment}"
  }
}

resource "aws_s3_bucket_public_access_block" "web" {
  bucket = aws_s3_bucket.web.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudFront Origin Access Control (OAC)
resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "${var.project_name}-web-oac-${var.environment}"
  description                       = "OAC para acceso exclusivo de CloudFront a S3"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# VPC origin: CloudFront llega al balanceador interno por la red privada de AWS
resource "aws_cloudfront_vpc_origin" "alb" {
  count = var.alb_arn != "" ? 1 : 0

  vpc_origin_endpoint_config {
    name                   = "${var.project_name}-alb-${var.environment}"
    arn                    = var.alb_arn
    http_port              = 80
    https_port             = 443
    origin_protocol_policy = "http-only"

    origin_ssl_protocols {
      items    = ["TLSv1.2"]
      quantity = 1
    }
  }
}

# Encabezados de seguridad para el portal y la API
resource "aws_cloudfront_response_headers_policy" "security" {
  name = "${var.project_name}-security-headers-${var.environment}"

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = false
      preload                    = false
      override                   = true
    }

    content_type_options {
      override = true
    }

    frame_options {
      frame_option = "DENY"
      override     = true
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }

    content_security_policy {
      content_security_policy = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
      override                = true
    }
  }
}

# Rutas del portal Angular: lo que no es un archivo se sirve como index.html, solo en el origen S3
resource "aws_cloudfront_function" "spa_routing" {
  name    = "${var.project_name}-spa-routing-${var.environment}"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = file("${path.module}/spa-routing.js")
}

# Distribución CloudFront global para Angular SPA
resource "aws_cloudfront_distribution" "web" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.web.bucket_regional_domain_name
    origin_id                = "S3Origin"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }

  dynamic "origin" {
    for_each = var.alb_arn != "" ? [1] : []
    content {
      domain_name = var.alb_dns_name
      origin_id   = "ALBOrigin"

      vpc_origin_config {
        vpc_origin_id = aws_cloudfront_vpc_origin.alb[0].id
      }
    }
  }

  dynamic "ordered_cache_behavior" {
    for_each = var.alb_arn != "" ? [1] : []
    content {
      path_pattern     = "/api/*"
      allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
      cached_methods   = ["GET", "HEAD", "OPTIONS"]
      target_origin_id = "ALBOrigin"

      forwarded_values {
        query_string = true
        headers      = ["Accept", "Accept-Language", "Authorization", "Content-Type", "Origin", "Referer", "User-Agent", "Idempotency-Key"]
        cookies {
          forward = "all"
        }
      }

      viewer_protocol_policy     = "redirect-to-https"
      response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id
      min_ttl                    = 0
      default_ttl                = 0
      max_ttl                    = 0
    }
  }

  dynamic "ordered_cache_behavior" {
    for_each = var.alb_arn != "" ? [1] : []
    content {
      path_pattern     = "/health"
      allowed_methods  = ["GET", "HEAD", "OPTIONS"]
      cached_methods   = ["GET", "HEAD"]
      target_origin_id = "ALBOrigin"

      forwarded_values {
        query_string = false
        headers      = ["Accept", "Origin"]
        cookies {
          forward = "none"
        }
      }

      viewer_protocol_policy     = "redirect-to-https"
      response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id
      min_ttl                    = 0
      default_ttl                = 0
      max_ttl                    = 0
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3Origin"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy     = "redirect-to-https"
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id
    min_ttl                    = 0
    default_ttl                = 3600
    max_ttl                    = 86400

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa_routing.arn
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${var.project_name}-cloudfront-${var.environment}"
  }
}

# Política en S3 que permite lectura únicamente a través de CloudFront OAC
resource "aws_s3_bucket_policy" "web" {
  bucket = aws_s3_bucket.web.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipalReadOnly"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.web.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.web.arn
          }
        }
      }
    ]
  })
}
