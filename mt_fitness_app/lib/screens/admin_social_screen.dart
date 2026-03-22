import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import '../widgets/premium_card.dart';

class AdminSocialScreen extends StatefulWidget {
  const AdminSocialScreen({super.key});

  @override
  State<AdminSocialScreen> createState() => _AdminSocialScreenState();
}

class _AdminSocialScreenState extends State<AdminSocialScreen> {
  List<dynamic> _posts = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadPosts();
  }

  Future<void> _loadPosts() async {
    setState(() => _isLoading = true);
    try {
      // In a real scenario, we'd add this to ApiService
      // For now, I'll simulate or add it to ApiService first
      final posts = await ApiService().getSocialPosts();
      setState(() {
        _posts = posts;
        _isLoading = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al cargar posts: $e')),
        );
      }
    }
  }

  Future<void> _approvePost(int id) async {
    try {
      await ApiService().approveSocialPost(id);
      _loadPosts();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Post aprobado con éxito')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  Future<void> _rejectPost(int id) async {
    try {
      await ApiService().rejectSocialPost(id);
      _loadPosts();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  Future<void> _generateNewProposal() async {
    setState(() => _isLoading = true);
    try {
      await ApiService().generateSocialProposal();
      _loadPosts();
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al generar: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgColor,
      appBar: AppBar(
        title: const Text('Gestión de Redes (IA)'),
        backgroundColor: AppTheme.surface,
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.refreshCw),
            onPressed: _loadPosts,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
          : Column(
              children: [
                _buildHeader(),
                Expanded(
                  child: _posts.isEmpty
                      ? const Center(child: Text('No hay propuestas pendientes', style: TextStyle(color: AppTheme.textMuted)))
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _posts.length,
                          itemBuilder: (context, index) {
                            final post = _posts[index];
                            return _buildPostCard(post);
                          },
                        ),
                ),
              ],
            ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      color: AppTheme.surface,
      child: Row(
        children: [
          const Icon(LucideIcons.bot, color: AppTheme.primary, size: 32),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Agente Social MT', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                Text('Gestiona tus propuestas automáticas', style: TextStyle(color: AppTheme.textMuted, fontSize: 13)),
              ],
            ),
          ),
          ElevatedButton.icon(
            onPressed: _generateNewProposal,
            icon: const Icon(LucideIcons.plus, size: 16),
            label: const Text('Generar'),
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primary),
          ),
        ],
      ),
    );
  }

  Widget _buildPostCard(dynamic post) {
    final status = post['status'] ?? 'DRAFT';
    final isDraft = status == 'DRAFT';

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: PremiumCard(
        padding: 0,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (post['image_url'] != null)
            ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              child: Image.network(
                post['image_url'],
                height: 150,
                width: double.infinity,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Container(
                  height: 150,
                  color: Colors.grey[900],
                  child: const Icon(LucideIcons.imageOff, color: AppTheme.textMuted),
                ),
              ),
            ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(post['title'] ?? 'Sin título', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: status == 'APPROVED' ? Colors.green.withOpacity(0.2) : (status == 'DRAFT' ? Colors.orange.withOpacity(0.2) : Colors.red.withOpacity(0.2)),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        status,
                        style: TextStyle(
                          fontSize: 10,
                          color: status == 'APPROVED' ? Colors.green : (status == 'DRAFT' ? Colors.orange : Colors.red),
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(post['caption'] ?? '', style: const TextStyle(fontSize: 13, height: 1.4)),
                const SizedBox(height: 16),
                if (isDraft)
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => _rejectPost(post['id']),
                          style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.red)),
                          child: const Text('Rechazar', style: TextStyle(color: Colors.red)),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () => _approvePost(post['id']),
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                          child: const Text('Aprobar'),
                        ),
                      ),
                    ],
                  ),
              ],
            ),
          ),
        ],
        ),
      ),
    );
  }
}
