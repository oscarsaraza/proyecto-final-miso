import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-cotizador',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="cotizador-container">
      <div class="cotizador-header">
        <h1>Cotizador de Seguros de Vida</h1>
        <p>Proceso comercial guiado: Identificación, Consentimiento, Cotización, Coberturas y Recaudo.</p>
      </div>

      <div class="steps-progress">
        <div class="step active">1. Identificación</div>
        <div class="step">2. Consentimiento</div>
        <div class="step">3. Tarificación</div>
        <div class="step">4. Coberturas</div>
        <div class="step">5. Emisión y Pago</div>
      </div>

      <div class="content-card">
        <h3>Estructura base del flujo comercial lista para desarrollo</h3>
        <p>Las siguientes historias de usuario implementarán cada paso de este componente:</p>
        <ul>
          <li><strong>HU-WEB-02:</strong> Captura de datos del cliente e identificación inicial.</li>
          <li><strong>HU-WEB-01:</strong> Captura y auditoría del consentimiento Open Finance.</li>
          <li><strong>HU-WEB-03 & 04:</strong> Cálculo de prima en memoria con degradación ante caída de burós.</li>
          <li><strong>HU-WEB-05:</strong> Configuración de coberturas y emisión contractual.</li>
          <li><strong>HU-WEB-06:</strong> Pago con garantía de idempotencia.</li>
        </ul>
      </div>
    </div>
  `,
  styles: [`
    .cotizador-container {
      max-width: 900px;
      margin: 32px auto;
      padding: 0 20px;
    }
    .cotizador-header h1 {
      margin: 0 0 6px;
      color: #0f172a;
      font-size: 26px;
    }
    .cotizador-header p {
      margin: 0 0 24px;
      color: #64748b;
    }
    .steps-progress {
      display: flex;
      gap: 12px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }
    .step {
      padding: 8px 16px;
      background: #f1f5f9;
      border-radius: 20px;
      font-size: 13px;
      color: #64748b;
      font-weight: 500;
    }
    .step.active {
      background: #0284c7;
      color: #ffffff;
    }
    .content-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    .content-card h3 {
      margin-top: 0;
      color: #1e293b;
    }
    .content-card ul {
      padding-left: 20px;
      color: #475569;
      line-height: 1.8;
    }
  `]
})
export class CotizadorComponent {}
