import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LoginComponent } from './login.component';

describe('LoginComponent (Placeholder HU-WEB-13)', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoginComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse el componente de login', () => {
    expect(component).toBeTruthy();
  });

  it('debe renderizar los campos para usuario, contraseña y código 2FA', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#username')).toBeTruthy();
    expect(compiled.querySelector('#password')).toBeTruthy();
    expect(compiled.querySelector('#totp')).toBeTruthy();
  });

  it('debe mostrar mensaje de placeholder informativo al ejecutar onSubmit', () => {
    component.onSubmit();
    expect(component.noticeMessage()).toContain('HU-WEB-13');
  });
});
