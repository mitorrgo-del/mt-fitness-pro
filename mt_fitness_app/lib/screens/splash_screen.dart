import 'package:flutter/material.dart';
import 'dart:async';
import 'login_screen.dart';

class SplashScreen extends StatefulWidget {
  @override
  _SplashScreenState createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with TickerProviderStateMixin {
  late AnimationController _zoomController;
  late Animation<double> _zoomAnimation;
  late AnimationController _auraController;

  @override
  void initState() {
    super.initState();
    
    // Zoom control: Estela y crecimiento expansivo
    _zoomController = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 2200));
        
    // Aura control: Reflejo móvil dorado alrededor de las letras
    _auraController = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1200))..repeat(reverse: true);

    // Mapeo del tamaño desde micro hasta cubrir el ancho de pantalla
    _zoomAnimation = Tween<double>(begin: 0.05, end: 1.05).animate(CurvedAnimation(
      parent: _zoomController,
      curve: Curves.easeOutExpo,
    ));

    _zoomController.forward();

    // Redirección inteligente al presenciar la animación completa
    Timer(const Duration(milliseconds: 3800), () {
      Navigator.of(context).pushReplacement(
        PageRouteBuilder(
          transitionDuration: const Duration(milliseconds: 1000),
          pageBuilder: (_, __, ___) => LoginScreen(),
          transitionsBuilder: (_, animation, __, child) => FadeTransition(opacity: animation, child: child),
        )
      );
    });
  }

  @override
  void dispose() {
    _zoomController.dispose();
    _auraController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF09090B), // Color puro acorde al branding V3
      body: Center(
        child: AnimatedBuilder(
          animation: Listenable.merge([_zoomController, _auraController]),
          builder: (context, child) {
            double screenWidth = MediaQuery.of(context).size.width; 
            
            return Transform.scale(
              scale: _zoomAnimation.value,
              child: Stack(
                alignment: Alignment.center,
                children: [
                   // Aura Activa Dorada
                   Container(
                     width: screenWidth * 0.8,
                     height: screenWidth * 0.8,
                     decoration: BoxDecoration(
                       shape: BoxShape.circle,
                       boxShadow: [
                         BoxShadow(
                           color: const Color(0xFFD4AF37).withOpacity(0.1 + (_auraController.value * 0.25)),
                           blurRadius: 40 + (_auraController.value * 50),
                           spreadRadius: 10 + (_auraController.value * 20),
                         ),
                         BoxShadow(
                           color: const Color(0xFFFFD700).withOpacity(0.05 + (_auraController.value * 0.1)),
                           blurRadius: 20 + (_auraController.value * 30),
                           spreadRadius: 5 + (_auraController.value * 10),
                         )
                       ]
                     )
                   ),
                   // El Logotipo Transparente
                   Image.asset(
                     'assets/images/logo_oro.png',
                     width: screenWidth * 0.9,
                     fit: BoxFit.contain,
                   )
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}
