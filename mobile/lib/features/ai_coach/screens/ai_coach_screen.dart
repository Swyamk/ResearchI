import 'package:dash_chat_2/dash_chat_2.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/api/api_client.dart';

class AiCoachScreen extends ConsumerStatefulWidget {
  const AiCoachScreen({super.key});
  @override
  ConsumerState<AiCoachScreen> createState() => _AiCoachScreenState();
}

class _AiCoachScreenState extends ConsumerState<AiCoachScreen> {
  final _sessionId = const Uuid().v4();
  final List<ChatMessage> _messages = [];
  bool _isTyping = false;

  late final ChatUser _user = ChatUser(id: 'user', firstName: 'You');
  late final ChatUser _ai = ChatUser(id: 'ai', firstName: 'NutriMind AI',
    profileImage: 'https://api.dicebear.com/7.x/bottts/png?seed=nutrimind');

  @override
  void initState() {
    super.initState();
    _addWelcome();
  }

  void _addWelcome() {
    _messages.add(ChatMessage(
      user: _ai,
      createdAt: DateTime.now(),
      text: "👋 Hi! I'm your NutriMind AI Coach powered by Gemini 2.5 Pro.\n\n"
            "I can help you analyze your meals, answer nutrition questions, "
            "create meal plans, and track your progress.\n\n"
            "What would you like to know today?",
    ));
  }

  Future<void> _send(ChatMessage msg) async {
    setState(() { _messages.insert(0, msg); _isTyping = true; });
    try {
      final data = await ref.read(apiClientProvider).chatWithCoach(msg.text, _sessionId);
      final reply = ChatMessage(
        user: _ai,
        createdAt: DateTime.now(),
        text: data['response'] ?? 'Sorry, I could not process that.',
      );
      if (mounted) setState(() { _messages.insert(0, reply); _isTyping = false; });
    } catch (_) {
      if (mounted) setState(() {
        _messages.insert(0, ChatMessage(user: _ai, createdAt: DateTime.now(),
          text: "I'm having trouble connecting. Please try again."));
        _isTyping = false;
      });
    }
  }

  Future<void> _getDailySummary() async {
    setState(() => _isTyping = true);
    try {
      final data = await ref.read(apiClientProvider).getDailySummary();
      final msg = ChatMessage(user: _ai, createdAt: DateTime.now(), text: data['summary'] ?? 'No summary available.');
      if (mounted) setState(() { _messages.insert(0, msg); _isTyping = false; });
    } catch (_) {
      if (mounted) setState(() => _isTyping = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 36, height: 36,
              decoration: BoxDecoration(gradient: AppTheme.primaryGradient, borderRadius: BorderRadius.circular(10)),
              child: const Icon(Icons.psychology_rounded, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('AI Coach', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                Row(children: [
                  Container(width: 6, height: 6, margin: const EdgeInsets.only(right: 4),
                    decoration: const BoxDecoration(color: AppTheme.primary, shape: BoxShape.circle)),
                  const Text('Gemini 2.5 Pro', style: TextStyle(color: AppTheme.primary, fontSize: 11)),
                ]),
              ],
            ),
          ],
        ),
        backgroundColor: AppTheme.background,
        actions: [
          TextButton.icon(
            onPressed: _getDailySummary,
            icon: const Icon(Icons.summarize_rounded, size: 16, color: AppTheme.primary),
            label: const Text('Summary', style: TextStyle(color: AppTheme.primary, fontSize: 12)),
          ),
        ],
      ),

      body: Column(
        children: [
          // Quick prompts
          SizedBox(
            height: 44,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              children: [
                for (final prompt in [
                  'What did I eat today?', 'Increase protein tips', 'Healthy meal plan',
                  'Am I meeting goals?', 'Weekly summary',
                ])
                  GestureDetector(
                    onTap: () => _send(ChatMessage(user: _user, createdAt: DateTime.now(), text: prompt)),
                    child: Container(
                      margin: const EdgeInsets.only(right: 8, top: 6, bottom: 6),
                      padding: const EdgeInsets.symmetric(horizontal: 14),
                      decoration: BoxDecoration(
                        color: AppTheme.surface2,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: const Color(0x1AFFFFFF)),
                      ),
                      child: Center(child: Text(prompt, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12))),
                    ),
                  ),
              ],
            ),
          ),

          // Chat
          Expanded(
            child: DashChat(
              currentUser: _user,
              messages: _messages,
              onSend: _send,
              typingUsers: _isTyping ? [_ai] : [],
              messageOptions: MessageOptions(
                currentUserContainerColor: AppTheme.primary.withOpacity(0.2),
                containerColor: AppTheme.surface2,
                currentUserTextColor: Colors.white,
                textColor: Colors.white,
                borderRadius: 16,
                messageTextBuilder: (msg, _, __) => Text(msg.text,
                  style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.4)),
              ),
              inputOptions: InputOptions(
                inputDecoration: InputDecoration(
                  hintText: 'Ask your AI nutrition coach...',
                  hintStyle: const TextStyle(color: AppTheme.textTertiary, fontSize: 14),
                  filled: true,
                  fillColor: AppTheme.surface2,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(20),
                    borderSide: const BorderSide(color: Color(0x1AFFFFFF)),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(20),
                    borderSide: const BorderSide(color: Color(0x1AFFFFFF)),
                  ),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                ),
                sendButtonBuilder: (send) => GestureDetector(
                  onTap: send,
                  child: Container(
                    width: 44, height: 44, margin: const EdgeInsets.only(left: 8),
                    decoration: BoxDecoration(gradient: AppTheme.primaryGradient, borderRadius: BorderRadius.circular(14)),
                    child: const Icon(Icons.send_rounded, color: Colors.white, size: 20),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
