import 'dart:ui';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class PremiumCard extends StatelessWidget {
  final Widget child;
  final double padding;
  final EdgeInsetsGeometry? margin;
  final LinearGradient? gradient;
  final bool glass;

  const PremiumCard({
    super.key,
    required this.child,
    this.padding = 20.0,
    this.margin,
    this.gradient,
    this.glass = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: margin,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: glass ? 12 : 0, sigmaY: glass ? 12 : 0),
          child: Container(
            width: double.infinity,
            padding: EdgeInsets.all(padding),
            decoration: BoxDecoration(
              color: gradient != null 
                  ? null 
                  : (glass ? AppTheme.surface.withOpacity(0.7) : AppTheme.surface),
              gradient: gradient,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: Colors.white.withOpacity(glass ? 0.1 : 0.05), 
                width: 1.5
              ),
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}
