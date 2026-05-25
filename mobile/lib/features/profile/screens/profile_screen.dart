import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/api/api_client.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});
  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  Map<String, dynamic>? _user;
  bool _loading = true;
  bool _saving = false;

  final _ageCtrl = TextEditingController();
  final _heightCtrl = TextEditingController();
  final _weightCtrl = TextEditingController();
  String _gender = 'male';
  String _goal = 'maintenance';
  String _activity = 'moderately_active';
  List<String> _conditions = [];
  List<String> _dietary = [];

  final _storage = const FlutterSecureStorage();

  static const _goals = ['weight_loss','muscle_gain','maintenance','diabetes_management','heart_health','general_wellness'];
  static const _activities = ['sedentary','lightly_active','moderately_active','very_active','extremely_active'];
  static const _conditionsList = ['diabetes_type1','diabetes_type2','hypertension','high_cholesterol','pcos','thyroid'];
  static const _dietaryList = ['vegetarian','vegan','gluten_free','dairy_free','halal','none'];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await ref.read(apiClientProvider).getMe();
      final p = data['profile'] ?? {};
      setState(() {
        _user = data;
        _ageCtrl.text = (p['age'] ?? '').toString();
        _heightCtrl.text = (p['height_cm'] ?? '').toString();
        _weightCtrl.text = (p['weight_kg'] ?? '').toString();
        _gender = p['gender'] ?? 'male';
        _goal = p['primary_goal'] ?? 'maintenance';
        _activity = p['activity_level'] ?? 'moderately_active';
        _conditions = List<String>.from(p['health_conditions'] ?? []);
        _dietary = List<String>.from(p['dietary_restrictions'] ?? []);
        _loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await ref.read(apiClientProvider).updateProfile({
        'age': int.tryParse(_ageCtrl.text),
        'gender': _gender,
        'height_cm': double.tryParse(_heightCtrl.text),
        'weight_kg': double.tryParse(_weightCtrl.text),
        'activity_level': _activity,
        'primary_goal': _goal,
        'health_conditions': _conditions,
        'dietary_restrictions': _dietary,
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Profile saved! Targets updated.'), backgroundColor: AppTheme.success),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Save failed. Try again.'), backgroundColor: AppTheme.error),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _logout() async {
    await _storage.delete(key: 'access_token');
    if (mounted) context.go('/auth/login');
  }

  Widget _chipGroup(String label, List<String> options, List<String> selected, Color activeColor, Function(String) onTap) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13, fontWeight: FontWeight.w500)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8, runSpacing: 8,
          children: options.map((o) {
            final isSelected = selected.contains(o);
            return GestureDetector(
              onTap: () => onTap(o),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: isSelected ? activeColor.withOpacity(0.15) : Colors.white.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: isSelected ? activeColor.withOpacity(0.5) : const Color(0x1AFFFFFF)),
                ),
                child: Text(o.replaceAll('_', ' '),
                  style: TextStyle(color: isSelected ? activeColor : AppTheme.textSecondary, fontSize: 12, fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal)),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(
      backgroundColor: AppTheme.background,
      body: Center(child: CircularProgressIndicator(color: AppTheme.primary)),
    );

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Health Profile'),
        backgroundColor: AppTheme.background,
        actions: [
          IconButton(icon: const Icon(Icons.logout_rounded, color: AppTheme.error), onPressed: _logout),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 120),
        children: [
          // Avatar card
          if (_user != null)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: AppTheme.glassCard,
              child: Row(
                children: [
                  Container(
                    width: 56, height: 56,
                    decoration: BoxDecoration(gradient: AppTheme.primaryGradient, borderRadius: BorderRadius.circular(16)),
                    child: Center(child: Text(
                      (_user!['full_name'] ?? 'U')[0].toUpperCase(),
                      style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w700, fontFamily: 'Outfit'),
                    )),
                  ),
                  const SizedBox(width: 14),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_user!['full_name'] ?? '', style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w700, fontSize: 16)),
                      Text(_user!['email'] ?? '', style: const TextStyle(color: AppTheme.textTertiary, fontSize: 13)),
                    ],
                  ),
                ],
              ),
            ).animate().fadeIn(),

          const SizedBox(height: 16),

          // Biometrics
          _Section(title: 'Biometrics', child: Column(
            children: [
              Row(children: [
                Expanded(child: _Field(ctrl: _ageCtrl, label: 'Age', type: TextInputType.number)),
                const SizedBox(width: 12),
                Expanded(child: _Field(ctrl: _heightCtrl, label: 'Height (cm)', type: TextInputType.number)),
                const SizedBox(width: 12),
                Expanded(child: _Field(ctrl: _weightCtrl, label: 'Weight (kg)', type: TextInputType.number)),
              ]),
              const SizedBox(height: 12),
              Row(children: [
                const Text('Gender:', style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                const SizedBox(width: 12),
                for (final g in ['male', 'female', 'other'])
                  GestureDetector(
                    onTap: () => setState(() => _gender = g),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      margin: const EdgeInsets.only(right: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                      decoration: BoxDecoration(
                        color: _gender == g ? AppTheme.primary.withOpacity(0.2) : Colors.white.withOpacity(0.05),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: _gender == g ? AppTheme.primary : const Color(0x1AFFFFFF)),
                      ),
                      child: Text(g[0].toUpperCase() + g.substring(1),
                        style: TextStyle(color: _gender == g ? AppTheme.primary : AppTheme.textSecondary, fontSize: 12)),
                    ),
                  ),
              ]),
            ],
          )),

          const SizedBox(height: 12),

          // Goal
          _Section(title: 'Primary Goal', child: _chipGroup('', _goals, [_goal], AppTheme.primary, (v) => setState(() => _goal = v))),

          const SizedBox(height: 12),

          // Activity
          _Section(title: 'Activity Level', child: _chipGroup('', _activities, [_activity], AppTheme.accent, (v) => setState(() => _activity = v))),

          const SizedBox(height: 12),

          // Health conditions
          _Section(title: 'Health Conditions', child: _chipGroup('', _conditionsList, _conditions, const Color(0xFFEF4444), (v) {
            setState(() { if (_conditions.contains(v)) _conditions.remove(v); else _conditions.add(v); });
          })),

          const SizedBox(height: 12),

          // Dietary
          _Section(title: 'Dietary Preferences', child: _chipGroup('', _dietaryList, _dietary, AppTheme.accent, (v) {
            setState(() { if (_dietary.contains(v)) _dietary.remove(v); else _dietary.add(v); });
          })),

          const SizedBox(height: 24),

          ElevatedButton.icon(
            onPressed: _saving ? null : _save,
            icon: _saving
              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
              : const Icon(Icons.save_rounded),
            label: Text(_saving ? 'Saving...' : 'Save & Recalculate Targets'),
          ).animate().fadeIn(delay: 300.ms),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  final String title;
  final Widget child;
  const _Section({required this.title, required this.child});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(16),
    decoration: AppTheme.glassCard,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600, fontSize: 15)),
        const SizedBox(height: 14),
        child,
      ],
    ),
  ).animate().fadeIn();
}

class _Field extends StatelessWidget {
  final TextEditingController ctrl;
  final String label;
  final TextInputType type;
  const _Field({required this.ctrl, required this.label, required this.type});
  @override
  Widget build(BuildContext context) => TextField(
    controller: ctrl,
    keyboardType: type,
    style: const TextStyle(color: AppTheme.textPrimary, fontSize: 14),
    decoration: InputDecoration(labelText: label, isDense: true),
  );
}
