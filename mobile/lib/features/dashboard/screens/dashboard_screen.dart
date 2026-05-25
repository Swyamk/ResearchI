import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:percent_indicator/percent_indicator.dart';
import '../../core/theme/app_theme.dart';
import '../../core/api/api_client.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});
  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  Map<String, dynamic>? _dashboard;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await ref.read(apiClientProvider).getDashboard();
      if (mounted) setState(() { _dashboard = data; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final d = _dashboard;
    return Scaffold(
      backgroundColor: AppTheme.background,
      body: RefreshIndicator(
        color: AppTheme.primary,
        onRefresh: _load,
        child: CustomScrollView(
          slivers: [
            // App Bar
            SliverAppBar(
              expandedHeight: 120,
              pinned: true,
              backgroundColor: AppTheme.background,
              flexibleSpace: FlexibleSpaceBar(
                background: Container(
                  padding: const EdgeInsets.fromLTRB(20, 60, 20, 0),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Good evening! 👋', style: Theme.of(context).textTheme.headlineMedium),
                            const SizedBox(height: 4),
                            const Text("Here's your nutrition today", style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
                          ],
                        ),
                      ),
                      // Streak badge
                      if (d != null)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: AppTheme.primary.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppTheme.primary.withOpacity(0.3)),
                          ),
                          child: Row(
                            children: [
                              const Text('🔥', style: TextStyle(fontSize: 16)),
                              const SizedBox(width: 4),
                              Text('${d['streak']?['current_streak'] ?? 0} days',
                                style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w600, fontSize: 13)),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),

            SliverPadding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 100),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  if (_loading) ...[
                    const SizedBox(height: 20),
                    const Center(child: CircularProgressIndicator(color: AppTheme.primary)),
                  ] else if (d == null) ...[
                    const SizedBox(height: 60),
                    const Center(child: Text('Could not load data. Pull to refresh.', style: TextStyle(color: AppTheme.textSecondary))),
                  ] else ...[
                    const SizedBox(height: 20),

                    // Calorie Card
                    _CalorieCard(
                      consumed: (d['today_calories'] ?? 0).toDouble(),
                      target: (d['calorie_target'] ?? 2000).toDouble(),
                    ).animate().fadeIn().slideY(begin: 0.1),
                    const SizedBox(height: 16),

                    // Macro cards
                    Row(
                      children: [
                        Expanded(child: _MacroCard('Protein', '${(d['today_protein_g'] ?? 0).toStringAsFixed(1)}g', AppTheme.proteinColor, Icons.fitness_center_rounded)),
                        const SizedBox(width: 10),
                        Expanded(child: _MacroCard('Carbs', '${(d['today_carbs_g'] ?? 0).toStringAsFixed(1)}g', AppTheme.carbsColor, Icons.grain_rounded)),
                        const SizedBox(width: 10),
                        Expanded(child: _MacroCard('Fat', '${(d['today_fat_g'] ?? 0).toStringAsFixed(1)}g', AppTheme.fatColor, Icons.water_drop_rounded)),
                      ],
                    ).animate().fadeIn(delay: 100.ms),
                    const SizedBox(height: 16),

                    // Quick Action
                    GestureDetector(
                      onTap: () => context.push('/camera'),
                      child: Container(
                        padding: const EdgeInsets.all(20),
                        decoration: AppTheme.primaryCard,
                        child: Row(
                          children: [
                            const Icon(Icons.camera_alt_rounded, color: Colors.white, size: 28),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text('Log a Meal', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16)),
                                  const SizedBox(height: 2),
                                  Text('Snap a photo for instant AI analysis', style: TextStyle(color: Colors.white.withOpacity(0.8), fontSize: 12)),
                                ],
                              ),
                            ),
                            const Icon(Icons.arrow_forward_ios_rounded, color: Colors.white, size: 16),
                          ],
                        ),
                      ),
                    ).animate().fadeIn(delay: 200.ms),
                    const SizedBox(height: 20),

                    // Recommendations
                    if (d['top_recommendations'] != null && (d['top_recommendations'] as List).isNotEmpty) ...[
                      const Text('AI Insights', style: TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 10),
                      for (final rec in (d['top_recommendations'] as List).take(3))
                        Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Container(
                            padding: const EdgeInsets.all(14),
                            decoration: AppTheme.glassCard,
                            child: Row(
                              children: [
                                const Icon(Icons.lightbulb_outline_rounded, color: AppTheme.primary, size: 18),
                                const SizedBox(width: 12),
                                Expanded(child: Text(rec.toString(), style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13))),
                              ],
                            ),
                          ).animate().fadeIn(delay: 300.ms),
                        ),
                    ],
                  ],
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CalorieCard extends StatelessWidget {
  final double consumed, target;
  const _CalorieCard({required this.consumed, required this.target});

  @override
  Widget build(BuildContext context) {
    final pct = target > 0 ? (consumed / target).clamp(0.0, 1.0) : 0.0;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: AppTheme.glassCard,
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Calories Today', style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
              Text('${(pct * 100).toStringAsFixed(0)}% of goal',
                style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w600, fontSize: 13)),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(consumed.toStringAsFixed(0),
                style: const TextStyle(color: AppTheme.textPrimary, fontSize: 42, fontWeight: FontWeight.w700, fontFamily: 'Outfit')),
              const SizedBox(width: 4),
              Text('/ ${target.toStringAsFixed(0)} kcal',
                style: const TextStyle(color: AppTheme.textTertiary, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 16),
          LinearPercentIndicator(
            percent: pct,
            lineHeight: 8,
            backgroundColor: Colors.white.withOpacity(0.1),
            linearGradient: const LinearGradient(colors: [AppTheme.primary, AppTheme.accent]),
            barRadius: const Radius.circular(4),
            padding: EdgeInsets.zero,
          ),
        ],
      ),
    );
  }
}

class _MacroCard extends StatelessWidget {
  final String label, value;
  final Color color;
  final IconData icon;
  const _MacroCard(this.label, this.value, this.color, this.icon);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: AppTheme.glassCard,
      child: Column(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 8),
          Text(value, style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 16, fontFamily: 'Outfit')),
          const SizedBox(height: 2),
          Text(label, style: const TextStyle(color: AppTheme.textTertiary, fontSize: 11)),
        ],
      ),
    );
  }
}
