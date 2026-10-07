module "vpc" {
  source = "./modules/vpc"

  project_name = var.project_name
  environment  = var.environment
}

module "alb" {
  source = "./modules/alb"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
}

module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
  environment  = var.environment
}

module "rds" {
  source = "./modules/rds"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  ecs_security_group_id = module.ecs.ecs_security_group_id
  db_username           = var.db_username
  db_password           = var.db_password
}

module "storage_events" {
  source = "./modules/storage_events"

  project_name = var.project_name
  environment  = var.environment
}

module "ecs" {
  source = "./modules/ecs"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  alb_security_group_id = module.alb.alb_security_group_id
  target_group_arn      = module.alb.target_group_arn
  ecr_image_url         = "${module.ecr.repository_url}:latest"
  db_host               = module.rds.address
  db_name               = module.rds.db_name
  db_user               = var.db_username
  db_password           = var.db_password
  sqs_queue_url         = module.storage_events.sqs_queue_url
  s3_bucket_name        = module.storage_events.s3_bucket_name
}

module "web_hosting" {
  source = "./modules/web_hosting"

  project_name = var.project_name
  environment  = var.environment
}
