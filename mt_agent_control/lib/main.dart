import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'dart:async';

void main() {
  runApp(const AgentControlApp());
}

class AppTheme {
  static const bg = Color(0xFF0D0D0D);
  static const surface = Color(0xFF1A1A1A);
  static const primary = Color(0xFFFF3366);
  static const accent = Color(0xFF2A2A2A);
  static const text = Colors.white;
  static const textMuted = Color(0xFF999999);
  static const success = Color(0xFF00E676);
}

class AgentControlApp extends StatelessWidget {
  const AgentControlApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MT Command Center',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: AppTheme.bg,
        colorScheme: const ColorScheme.dark(
          primary: AppTheme.primary,
          surface: AppTheme.surface,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: AppTheme.surface,
          elevation: 0,
          centerTitle: true,
        ),
      ),
      home: const DashboardScreen(),
    );
  }
}

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  // Configured to point directly to the active localtunnel backend
  final String apiUrl = "https://maintains-gibraltar-weekend-enabling.trycloudflare.com/api/agent";
  List<dynamic> _pendingPosts = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadPendingPosts();
  }

  Future<void> _loadPendingPosts() async {
    try {
      final response = await http.get(Uri.parse('$apiUrl/pending_posts'));
      if (response.statusCode == 200) {
        setState(() {
          _pendingPosts = jsonDecode(response.body);
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _approvePost(int id) async {
    await http.post(Uri.parse('$apiUrl/approve_post/$id'));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('✅ Aprobado. El autómata lo subirá en breve.'),
        backgroundColor: AppTheme.success,
      )
    );
    _loadPendingPosts();
  }

  Future<void> _rejectPost(int id) async {
    await http.post(Uri.parse('$apiUrl/reject_post/$id'));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('🗑️ Post descartado.'),
        backgroundColor: AppTheme.primary,
      )
    );
    _loadPendingPosts();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 10,
              height: 10,
              decoration: BoxDecoration(
                color: AppTheme.success,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.success.withOpacity(0.5),
                    spreadRadius: 2,
                    blurRadius: 5,
                  )
                ]
              ),
            ),
            const SizedBox(width: 10),
            const Text('Comandancia MT', style: TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.refresh_cw, color: AppTheme.textMuted),
            onPressed: () {
               setState(() => _isLoading = true);
               _loadPendingPosts();
            },
            tooltip: 'Refrescar',
          )
        ],
      ),
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
        : _pendingPosts.isEmpty 
          ? _buildEmptyState() 
          : _buildPendingList(),
      floatingActionButton: FloatingActionButton(
        backgroundColor: AppTheme.primary,
        child: const Icon(LucideIcons.message_square, color: Colors.white),
        onPressed: () => _openAgentChat(context),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(LucideIcons.bot, size: 80, color: AppTheme.textMuted.withOpacity(0.3)),
          const SizedBox(height: 16),
          const Text(
            'Todos los agentes están operando.\nNo hay tareas pendientes de aprobación.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppTheme.textMuted, fontSize: 16),
          ),
        ],
      ),
    );
  }

  Widget _buildPendingList() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _pendingPosts.length,
      itemBuilder: (context, index) {
        final post = _pendingPosts[index];
        return Card(
          color: AppTheme.surface,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          elevation: 0,
          margin: const EdgeInsets.only(bottom: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const Icon(LucideIcons.instagram, color: AppTheme.primary),
                    const SizedBox(width: 8),
                    Text(post['target'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    const Spacer(),
                    Text(post['created_at'], style: const TextStyle(color: AppTheme.textMuted, fontSize: 12)),
                  ],
                ),
              ),
              
              // Image Placeholder (Using local asset or network)
              Container(
                height: 250,
                width: double.infinity,
                color: AppTheme.accent,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(LucideIcons.cpu, size: 40, color: AppTheme.textMuted),
                    const SizedBox(height: 8),
                    Text('Generando Imagen AI...', style: TextStyle(color: AppTheme.textMuted.withOpacity(0.8))),
                  ],
                ),
              ),
              
              // Caption & Hashtags
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(post['caption'], style: const TextStyle(height: 1.4)),
                    const SizedBox(height: 12),
                    Text(post['hashtags'], style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),

              // Action Buttons
              Padding(
                padding: const EdgeInsets.only(left: 16, right: 16, bottom: 16),
                child: Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppTheme.text,
                          side: const BorderSide(color: AppTheme.accent, width: 2),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        onPressed: () => _rejectPost(post['id']),
                        icon: const Icon(LucideIcons.x, size: 18),
                        label: const Text('Rechazar'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.primary,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        onPressed: () => _approvePost(post['id']),
                        icon: const Icon(LucideIcons.check, size: 18),
                        label: const Text('Publicar', style: TextStyle(fontWeight: FontWeight.bold)),
                      ),
                    ),
                  ],
                ),
              )
            ],
          ),
        );
      },
    );
  }

  void _openAgentChat(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => const AgentChatSheet(),
    );
  }
}

class AgentChatSheet extends StatefulWidget {
  const AgentChatSheet({super.key});

  @override
  State<AgentChatSheet> createState() => _AgentChatSheetState();
}

class _AgentChatSheetState extends State<AgentChatSheet> {
  final TextEditingController _cmdController = TextEditingController();
  final List<Map<String, dynamic>> _messages = [
    {"text": "Autómata conectado. A la espera de instrucciones directas, Miky.", "isUser": false}
  ];

  void _sendMsg() async {
    if (_cmdController.text.trim().isEmpty) return;
    final text = _cmdController.text.trim();
    setState(() {
      _messages.add({"text": text, "isUser": true});
      _cmdController.clear();
      _messages.add({"text": "Procesando instrucción a través del Agente Local...", "isUser": false});
    });
    
    try {
      final res = await http.post(
        Uri.parse('https://maintains-gibraltar-weekend-enabling.trycloudflare.com/api/agent/chat'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({"message": text})
      );
      
      setState(() {
         _messages.removeLast();
         if(res.statusCode == 200) {
           _messages.add({"text": "¡Orden cumplida, Miky! He analizado tu petición '$text' y he dejado la propuesta terminada en tu cola del Dashboard.\n\nCierra este chat y desliza hacia abajo (o dale a Refrescar) en la ventana principal para ver y aprobar el post de Instagram.", "isUser": false});
         } else {
           _messages.add({"text": "Hubo un error al procesar tu petición en el cerebro local.", "isUser": false});
         }
      });
    } catch (e) {
       setState(() {
          _messages.removeLast();
          _messages.add({"text": "Error de conexión con el Servidor: $e", "isUser": false});
       });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.85,
      decoration: const BoxDecoration(
        color: AppTheme.bg,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        children: [
          // Handle
          Container(
            margin: const EdgeInsets.only(top: 12, bottom: 20),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppTheme.accent,
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              children: [
                Icon(LucideIcons.terminal, color: AppTheme.primary),
                SizedBox(width: 10),
                Text('Terminal de Agentes', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
          ),
          const Divider(color: AppTheme.accent),
          
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(20),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                return Align(
                  alignment: msg['isUser'] ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(14),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
                    decoration: BoxDecoration(
                      color: msg['isUser'] ? AppTheme.primary : AppTheme.surface,
                      borderRadius: BorderRadius.circular(14),
                      border: msg['isUser'] ? null : Border.all(color: AppTheme.accent),
                    ),
                    child: Text(msg['text'], style: const TextStyle(fontSize: 15)),
                  ),
                );
              },
            ),
          ),
          
          // Input box
          Padding(
            padding: EdgeInsets.only(
              left: 20, right: 20, bottom: MediaQuery.of(context).viewInsets.bottom + 20, top: 10
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _cmdController,
                    decoration: InputDecoration(
                      hintText: 'Ordena a los agentes...',
                      hintStyle: const TextStyle(color: AppTheme.textMuted),
                      filled: true,
                      fillColor: AppTheme.surface,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(30),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                    ),
                    onSubmitted: (_) => _sendMsg(),
                  ),
                ),
                const SizedBox(width: 10),
                GestureDetector(
                  onTap: _sendMsg,
                  child: Container(
                    width: 50,
                    height: 50,
                    decoration: const BoxDecoration(
                      color: AppTheme.primary,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(LucideIcons.send, color: Colors.white, size: 20),
                  ),
                )
              ],
            ),
          )
        ],
      ),
    );
  }
}
