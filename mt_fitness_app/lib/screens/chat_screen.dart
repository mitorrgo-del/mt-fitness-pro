import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _messageController = TextEditingController();
  final List<Map<String, dynamic>> _messages = [];
  bool _isLoading = true;
  bool _isTyping = false;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _loadMessages();
  }

  Future<void> _loadMessages() async {
    try {
      final messages = await ApiService().getChatMessages();
      setState(() {
        _messages.clear();
        _messages.addAll(messages.cast<Map<String, dynamic>>());
        _isLoading = false;
      });
      _scrollToBottom();
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _handleSend() async {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    _messageController.clear();
    setState(() {
      _messages.add({
        'content': text,
        'sender_role': 'CLIENT',
        'timestamp': DateTime.now().toIso8601String(),
      });
      _isTyping = true;
    });
    _scrollToBottom();

    try {
      final response = await ApiService().sendChatMessage(text);
      
      // If server returns the response immediately
      if (response.containsKey('response')) {
         setState(() {
           _isTyping = false;
           _messages.add({
             'content': response['response'],
             'sender_role': 'BOT',
             'timestamp': DateTime.now().toIso8601String(),
           });
         });
      } else {
        // Fallback or just reload
         await _loadMessages();
         setState(() => _isTyping = false);
      }
      _scrollToBottom();
    } catch (e) {
      setState(() => _isTyping = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error al enviar: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Coach Miguel Torres'),
        leading: Navigator.of(context).canPop() 
           ? IconButton(
              icon: const Icon(LucideIcons.chevronLeft),
              onPressed: () => Navigator.of(context).pop(),
             )
           : null,
      ),
      body: Column(
        children: [
          Expanded(
            child: _isLoading 
              ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
              : ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: _messages.length,
                  itemBuilder: (context, index) {
                    final msg = _messages[index];
                    final role = msg['sender_role'] ?? 'CLIENT';
                    final isMe = role == 'CLIENT' || role == 'USER';
                    return _buildMessageBubble(msg['content'] ?? '', isMe);
                  },
                ),
          ),
          if (_isTyping)
             Padding(
               padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
               child: Row(
                 children: [
                   const Text('Miguel Torres está escribiendo...', style: TextStyle(color: AppTheme.textMuted, fontSize: 12, fontStyle: FontStyle.italic)),
                   const SizedBox(width: 8),
                   SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primary.withOpacity(0.5))),
                 ],
               ),
             ),
          _buildInputArea(),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(String text, bool isMe) {
    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: isMe ? AppTheme.primary : AppTheme.surface,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isMe ? 16 : 0),
            bottomRight: Radius.circular(isMe ? 0 : 16),
          ),
          border: isMe ? null : Border.all(color: AppTheme.border),
        ),
        child: Text(
          text,
          style: TextStyle(
            color: isMe ? Colors.white : AppTheme.text,
            fontSize: 15,
          ),
        ),
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 12,
        bottom: 24, // More padding for bottom safety
      ),
      decoration: const BoxDecoration(
        color: Color(0xFF111111),
        border: Border(top: BorderSide(color: AppTheme.border)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _messageController,
              decoration: InputDecoration(
                hintText: 'Escribe al coach...',
                hintStyle: const TextStyle(fontSize: 14),
                filled: true,
                fillColor: AppTheme.surface,
                contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(25),
                  borderSide: const BorderSide(color: AppTheme.border),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(25),
                  borderSide: const BorderSide(color: AppTheme.primary),
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          CircleAvatar(
            backgroundColor: AppTheme.primary,
            child: IconButton(
              icon: const Icon(LucideIcons.send, color: Colors.white, size: 20),
              onPressed: _handleSend,
            ),
          ),
        ],
      ),
    );
  }
}
