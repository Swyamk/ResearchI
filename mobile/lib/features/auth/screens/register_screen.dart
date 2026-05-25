import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';
import '../../core/api/api_client.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});
  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _pwCtrl = TextEditingController();
  final _confirmCtrl = TextEditingController();
  bool _loading = false;
  final _storage = const FlutterSecureStorage();

  Future<void> _register() async {
    if (_pwCtrl.text != _confirmCtrl.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Passwords don't match"), backgroundColor: AppTheme.error),
      );
      return;
    }
    setState(() => _loading = true);
    try {
      final api = ref.read(apiClientProvider);
      final data = await api.register(_nameCtrl.text.trim(), _emailCtrl.text.trim(), _pwCtrl.text);
      await _storage.write(key: 'access_token', value: data['access_token']);
      if (mounted) context.go('/profile');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Registration failed. Try a different email.'), backgroundColor: AppTheme.error),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: AppTheme.backgroundGradient),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 32),
                Text('Create Account', style: Theme.of(context).textTheme.displayMedium,
                ).animate().fadeIn(),
                const SizedBox(height: 8),
                Text('Start your nutrition intelligence journey',
                  style: Theme.of(context).textTheme.bodyMedium,
                ).animate().fadeIn(delay: 100.ms),
                const SizedBox(height: 36),

                for (final f in [
                  (ctrl: _nameCtrl, label: 'Full Name', icon: Icons.person_outline, type: TextInputType.name, obscure: false),
                  (ctrl: _emailCtrl, label: 'Email', icon: Icons.email_outlined, type: TextInputType.emailAddress, obscure: false),
                  (ctrl: _pwCtrl, label: 'Password', icon: Icons.lock_outline, type: TextInputType.text, obscure: true),
                  (ctrl: _confirmCtrl, label: 'Confirm Password', icon: Icons.lock_outline, type: TextInputType.text, obscure: true),
                ]) ...[
                  TextField(
                    controller: f.ctrl,
                    keyboardType: f.type,
                    obscureText: f.obscure,
                    style: const TextStyle(color: AppTheme.textPrimary),
                    decoration: InputDecoration(
                      labelText: f.label,
                      prefixIcon: Icon(f.icon, color: AppTheme.textTertiary),
                    ),
                  ).animate().fadeIn(delay: 200.ms).slideX(begin: -0.05),
                  const SizedBox(height: 14),
                ],

                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: _loading ? null : _register,
                  child: _loading
                    ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Text('Create Free Account'),
                ).animate().fadeIn(delay: 600.ms),
                const SizedBox(height: 20),

                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text('Already have an account? ', style: TextStyle(color: AppTheme.textSecondary)),
                    GestureDetector(
                      onTap: () => context.go('/auth/login'),
                      child: const Text('Sign in', style: TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w600)),
                    ),
                  ],
                ).animate().fadeIn(delay: 700.ms),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
