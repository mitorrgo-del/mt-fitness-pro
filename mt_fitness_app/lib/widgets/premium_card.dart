import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class PremiumCard extends StatelessWidget {
  final Widget child;
  final double padding;
  final EdgeInsetsGeometry? margin;
  final LinearGradient? gradient;

  const PremiumCard({
    super.key,
    required this.child,
    this.padding = 16.0,
    this.margin,
    this.gradient,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(padding),
      margin: margin,
      decoration: BoxDecoration(
        color: gradient == null ? AppTheme.surface : null,
        gradient: gradient,
        borderRadius: BorderRadius.circular(16),
        border: gradient == null ? Border.all(color: AppTheme.border, width: 1) : null,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: child,
    );
  }
}
