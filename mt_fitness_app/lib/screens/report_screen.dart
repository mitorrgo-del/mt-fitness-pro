import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import '../widgets/premium_card.dart';

class ReportScreen extends StatefulWidget {
  const ReportScreen({super.key});

  @override
  State<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  final _weightController = TextEditingController();
  File? _photoFront;
  File? _photoSide;
  File? _photoBack;
  bool _isSubmitting = false;

  Future<void> _pickImage(int type) async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery, imageQuality: 50);
    if (pickedFile != null) {
      setState(() {
        if (type == 0) _photoFront = File(pickedFile.path);
        else if (type == 1) _photoSide = File(pickedFile.path);
        else _photoBack = File(pickedFile.path);
      });
    }
  }

  Future<void> _submit() async {
    if (_weightController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Por favor, indica tu peso')));
      return;
    }
    setState(() => _isSubmitting = true);
    try {
      await ApiService().submitReport(
        _weightController.text, 
        _photoFront?.path, 
        _photoSide?.path,
        _photoBack?.path
      );
      if (!mounted) return;
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Reporte enviado correctamente. El Coach revisará tu progreso.')));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('REPORTE SEMANAL VIP'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Image.network('https://www.mtfitness.es/logo.png', height: 60, color: Colors.white),
            const SizedBox(height: 32),
            const Text(
              'REPORTE DE PROGRESO',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, letterSpacing: 1.2),
            ),
            const SizedBox(height: 8),
            const Text(
              'Completa tus datos para que el Coach pueda ajustar tu plan.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppTheme.textMuted),
            ),
            const SizedBox(height: 40),
            
            PremiumCard(
              padding: 24,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   const Text('PESO DE ESTA SEMANA', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.primary)),
                   const SizedBox(height: 12),
                   TextField(
                     controller: _weightController,
                     keyboardType: TextInputType.number,
                     decoration: const InputDecoration(
                       hintText: 'Ej: 78.5',
                       suffixText: 'kg',
                     ),
                   ),
                ],
              ),
            ),
            
            const SizedBox(height: 32),
            const Text('FOTOS DE PROGRESO (Obligatorio)', style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primary)),
            const SizedBox(height: 16),
            
            Row(
              children: [
                Expanded(child: _buildPhotoUpload('FRENTE', _photoFront, 0)),
                const SizedBox(width: 8),
                Expanded(child: _buildPhotoUpload('PERFIL', _photoSide, 1)),
                const SizedBox(width: 8),
                Expanded(child: _buildPhotoUpload('ESPALDA', _photoBack, 2)),
              ],
            ),
            
            const SizedBox(height: 48),
            ElevatedButton(
              onPressed: _isSubmitting ? null : _submit,
              style: ElevatedButton.styleFrom(
                minimumSize: const Size(double.infinity, 54),
                backgroundColor: AppTheme.primary,
              ),
              child: _isSubmitting 
                ? const CircularProgressIndicator(color: Colors.white)
                : const Text('ENVIAR REPORTE AL COACH', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 20),
            const Text(
              '* Este reporte será revisado por tu Coach directamente.',
              style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPhotoUpload(String label, File? image, int type) {
    final Map<int, IconData> icons = {
      0: LucideIcons.user,
      1: LucideIcons.userPlus,
      2: LucideIcons.userCheck
    };
    return Column(
      children: [
        Text(label,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 10)),
        const SizedBox(height: 8),
        GestureDetector(
          onTap: () => _pickImage(type),
          child: Container(
            height: 140,
            width: double.infinity,
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.border),
            ),
            child: image != null
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.file(image, fit: BoxFit.cover))
                : Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(icons[type],
                          color: AppTheme.primary.withOpacity(0.5), size: 30),
                      const SizedBox(height: 8),
                      const Text('Añadir',
                          style: TextStyle(color: AppTheme.textMuted, fontSize: 9)),
                    ],
                  ),
          ),
        ),
      ],
    );
  }
}
