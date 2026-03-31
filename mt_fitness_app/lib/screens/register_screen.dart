import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _nameController = TextEditingController();
  final _surnameController = TextEditingController();
  final _emailController = TextEditingController();
  final _ageController = TextEditingController();
  final _heightController = TextEditingController();
  final _weightController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  
  bool _isLoading = false;
  bool _obscurePassword = true;

  Future<void> _handleRegister() async {
    if (_emailController.text.isEmpty || 
        _passwordController.text.isEmpty || 
        _nameController.text.isEmpty ||
        _surnameController.text.isEmpty ||
        _ageController.text.isEmpty ||
        _heightController.text.isEmpty ||
        _weightController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Por favor, rellena todos los campos')),
      );
      return;
    }

    if (_passwordController.text != _confirmPasswordController.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Las contraseñas no coinciden')),
      );
      return;
    }

    setState(() => _isLoading = true);
    
    try {
      final regData = {
        'name': _nameController.text.trim(),
        'surname': _surnameController.text.trim(),
        'email': _emailController.text.trim(),
        'password': _passwordController.text,
        'age': int.tryParse(_ageController.text) ?? 0,
        'height': double.tryParse(_heightController.text) ?? 0.0,
        'current_weight': double.tryParse(_weightController.text) ?? 0.0,
      };

      final response = await ApiService().register(regData);

      if (response.containsKey('error')) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(response['error'])),
        );
      } else {
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            backgroundColor: AppTheme.surface,
            title: Text('Registro Enviado', style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.bold)),
            content: const Text(
              'Tu solicitud ha sido enviada al Coach. Recibirás un correo una vez que se verifique tu pago y se apruebe tu acceso.',
              style: TextStyle(color: AppTheme.textMuted),
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.of(context).pop(); // dialog
                  Navigator.of(context).pop(); // back to login
                },
                child: const Text('Entendido', style: TextStyle(color: AppTheme.primary)),
              )
            ],
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error de conexión: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(LucideIcons.chevronLeft, color: Colors.white),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Text('Crear Cuenta', style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
      ),
      extendBodyBehindAppBar: true,
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          color: AppTheme.bgColor,
          gradient: AppTheme.surfaceGradient,
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _buildField(LucideIcons.user, 'Nombre', _nameController),
                const SizedBox(height: 16),
                _buildField(LucideIcons.user, 'Apellidos', _surnameController),
                const SizedBox(height: 16),
                _buildField(LucideIcons.mail, 'Email', _emailController, keyboardType: TextInputType.emailAddress),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(child: _buildField(LucideIcons.calendar, 'Edad', _ageController, keyboardType: TextInputType.number)),
                    const SizedBox(width: 16),
                    Expanded(child: _buildField(LucideIcons.ruler, 'Estatura (cm)', _heightController, keyboardType: TextInputType.number)),
                  ],
                ),
                const SizedBox(height: 16),
                _buildField(LucideIcons.activity, 'Peso Actual (kg)', _weightController, keyboardType: TextInputType.number),
                const SizedBox(height: 16),
                _buildField(LucideIcons.lock, 'Contraseña', _passwordController, isPassword: true),
                const SizedBox(height: 16),
                _buildField(LucideIcons.lock, 'Confirmar Contraseña', _confirmPasswordController, isPassword: true),
                const SizedBox(height: 40),
                
                ElevatedButton(
                  onPressed: _isLoading ? null : _handleRegister,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.all(18),
                    backgroundColor: AppTheme.primary,
                    shape: RoundedRectangleApp.rounded16,
                  ),
                  child: _isLoading 
                    ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2))
                    : Text(
                        'SOLICITAR ACCESO',
                        style: GoogleFonts.outfit(
                          fontSize: 16,
                          fontWeight: FontWeight.w900,
                          color: Colors.black,
                          letterSpacing: 1.2,
                        ),
                      ),
                ),
                const SizedBox(height: 20),
                Text(
                  'Un Coach revisará tu perfil y te dará acceso tras el pago.',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.outfit(
                    fontSize: 12,
                    color: AppTheme.textMuted,
                  ),
                ),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildField(IconData icon, String hint, TextEditingController controller, {TextInputType? keyboardType, bool isPassword = false}) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      obscureText: isPassword && _obscurePassword,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        hintText: hint,
        prefixIcon: Icon(icon, size: 20, color: AppTheme.primary),
        suffixIcon: isPassword ? IconButton(
          icon: Icon(_obscurePassword ? LucideIcons.eye : LucideIcons.eyeOff, size: 20, color: AppTheme.textMuted),
          onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
        ) : null,
      ),
    );
  }
}

class RoundedRectangleApp {
  static final rounded16 = RoundedRectangleBorder(borderRadius: BorderRadius.circular(16));
}
