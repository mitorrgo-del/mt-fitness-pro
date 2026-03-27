import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import '../widgets/premium_card.dart';
import 'admin_plan_editor.dart';

class AdminUsersScreen extends StatefulWidget {
  const AdminUsersScreen({super.key});

  @override
  State<AdminUsersScreen> createState() => _AdminUsersScreenState();
}

class _AdminUsersScreenState extends State<AdminUsersScreen> {
  bool _isLoading = true;
  List<dynamic> _users = [];

  @override
  void initState() {
    super.initState();
    _loadUsers();
  }

  Future<void> _loadUsers() async {
    final users = await ApiService().getAllUsers();
    setState(() {
      _users = users;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Panel de Control Coach'),
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
        : ListView.builder(
            padding: const EdgeInsets.all(20),
            itemCount: _users.length,
            itemBuilder: (context, index) {
              final user = _users[index];
              return Padding(
                padding: const EdgeInsets.only(bottom: 12.0),
                child: PremiumCard(
                  padding: 16,
                  child: Column(
                    children: [
                      Row(
                        children: [
                          CircleAvatar(
                            backgroundColor: AppTheme.primary.withOpacity(0.1),
                            child: Text(user['name'][0].toUpperCase(), style: const TextStyle(color: AppTheme.primary)),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Text(user['name'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                    const SizedBox(width: 8),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: user['status'] == 'APPROVED' ? Colors.green.withOpacity(0.1) : Colors.orange.withOpacity(0.1),
                                        borderRadius: BorderRadius.circular(10),
                                        border: Border.all(color: user['status'] == 'APPROVED' ? Colors.green : Colors.orange, width: 0.5),
                                      ),
                                      child: Text(
                                        user['status'] == 'APPROVED' ? 'ACTIVO' : 'PENDIENTE',
                                        style: TextStyle(color: user['status'] == 'APPROVED' ? Colors.green : Colors.orange, fontSize: 10, fontWeight: FontWeight.bold),
                                      ),
                                    ),
                                    if (user['status'] == 'APPROVED') ...[
                                      const SizedBox(width: 8),
                                      Text(
                                        '(${user['days_left']} d)',
                                        style: const TextStyle(fontSize: 12, color: AppTheme.textMuted, fontWeight: FontWeight.bold),
                                      ),
                                    ],
                                  ],
                                ),
                                Text(user['email'], style: const TextStyle(color: AppTheme.textMuted, fontSize: 12)),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: const Icon(LucideIcons.edit, color: AppTheme.primary, size: 20),
                            onPressed: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => AdminPlanEditor(
                                    userId: user['id'],
                                    userName: user['name'],
                                  ),
                                ),
                              ).then((_) => _loadUsers());
                            },
                          ),
                        ],
                      ),
                      if (user['status'] != 'APPROVED') ...[
                        const SizedBox(height: 12),
                        const Divider(height: 1),
                        const SizedBox(height: 8),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: () async {
                              await ApiService().approveUser(user['id']);
                              _loadUsers();
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.primary,
                              minimumSize: const Size(double.infinity, 36),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            ),
                            child: const Text('APROBAR CLIENTE', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            },
          ),
    );
  }
}
