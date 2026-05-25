import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/api/api_client.dart';

class AnalyticsScreen extends ConsumerStatefulWidget {
  const AnalyticsScreen({super.key});
  @override
  ConsumerState<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends ConsumerState<AnalyticsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  Map<String, dynamic>? _weekly;
  Map<String, dynamic>? _trend;
  Map<String, dynamic>? _deficiencies;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 2, vsync: this);
    _load();
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final api = ref.read(apiClientProvider);
      final results = await Future.wait([
        api.getWeeklySummary(),
        api.getNutritionTrend(days: 14),
        api.getRecommendations(),
      ]);
      if (mounted) {
        setState(() {
          _weekly = results[0];
          _trend = results[1];
          _deficiencies = results[2];
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Nutrition Analytics'),
        backgroundColor: AppTheme.background,
        bottom: TabBar(
          controller: _tabs,
          indicatorColor: AppTheme.primary,
          labelColor: AppTheme.primary,
          unselectedLabelColor: AppTheme.textTertiary,
          tabs: const [Tab(text: 'Weekly'), Tab(text: 'Trends')],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
          : TabBarView(
              controller: _tabs,
              children: [
                _WeeklyTab(weekly: _weekly),
                _TrendsTab(trend: _trend),
              ],
            ),
    );
  }
}

// ── Weekly Tab ────────────────────────────────────────────────────────────────
class _WeeklyTab extends StatelessWidget {
  final Map<String, dynamic>? weekly;
  const _WeeklyTab({this.weekly});

  @override
  Widget build(BuildContext context) {
    final w = weekly;
    if (w == null) return const Center(child: Text('No data', style: TextStyle(color: AppTheme.textSecondary)));

    final stats = [
      ('Avg Calories', '${(w['avg_daily_calories'] ?? 0).toStringAsFixed(0)} kcal', AppTheme.calorieColor),
      ('Avg Protein', '${(w['avg_daily_protein_g'] ?? 0).toStringAsFixed(1)}g', AppTheme.proteinColor),
      ('Days Logged', '${w['days_logged'] ?? 0} / 7', AppTheme.primary),
      ('Consistency', '${(w['consistency_score'] ?? 0).toStringAsFixed(0)}%', AppTheme.accent),
    ];

    return RefreshIndicator(
      color: AppTheme.primary,
      onRefresh: () async {},
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 100),
        children: [
          // Stat grid
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.6,
            children: stats.map((s) => Container(
              padding: const EdgeInsets.all(16),
              decoration: AppTheme.glassCard,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(s.$1, style: const TextStyle(color: AppTheme.textTertiary, fontSize: 12)),
                  const SizedBox(height: 8),
                  Text(s.$2, style: TextStyle(color: s.$3, fontWeight: FontWeight.w700, fontSize: 20, fontFamily: 'Outfit')),
                ],
              ),
            ).animate().fadeIn().scale(begin: const Offset(0.95, 0.95))).toList(),
          ),

          const SizedBox(height: 20),

          // Macro breakdown bar
          Container(
            padding: const EdgeInsets.all(16),
            decoration: AppTheme.glassCard,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Avg Daily Macros', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600, fontSize: 15)),
                const SizedBox(height: 16),
                for (final macro in [
                  ('Protein', w['avg_daily_protein_g'] ?? 0, AppTheme.proteinColor),
                  ('Carbs', w['avg_daily_carbs_g'] ?? 0, AppTheme.carbsColor),
                  ('Fat', w['avg_daily_fat_g'] ?? 0, AppTheme.fatColor),
                ]) ...[
                  Row(
                    children: [
                      SizedBox(width: 60, child: Text(macro.$1, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13))),
                      Expanded(
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(4),
                          child: LinearProgressIndicator(
                            value: ((macro.$2 as num).toDouble() / 200).clamp(0.0, 1.0),
                            backgroundColor: Colors.white10,
                            valueColor: AlwaysStoppedAnimation<Color>(macro.$3),
                            minHeight: 8,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text('${(macro.$2 as num).toStringAsFixed(1)}g',
                        style: TextStyle(color: macro.$3, fontWeight: FontWeight.w600, fontSize: 13)),
                    ],
                  ),
                  const SizedBox(height: 12),
                ],
              ],
            ),
          ).animate().fadeIn(delay: 200.ms),
        ],
      ),
    );
  }
}

// ── Trends Tab ────────────────────────────────────────────────────────────────
class _TrendsTab extends StatelessWidget {
  final Map<String, dynamic>? trend;
  const _TrendsTab({this.trend});

  @override
  Widget build(BuildContext context) {
    final calories = (trend?['calories'] as List?)?.map((e) => (e as num).toDouble()).toList() ?? [];
    if (calories.isEmpty) {
      return const Center(child: Text('Log meals to see trends', style: TextStyle(color: AppTheme.textSecondary)));
    }

    final spots = calories.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value)).toList();
    final avg = calories.reduce((a, b) => a + b) / calories.length;

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 100),
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: AppTheme.glassCard,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('14-Day Calorie Trend', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600, fontSize: 15)),
              const SizedBox(height: 4),
              Text('Avg: ${avg.toStringAsFixed(0)} kcal/day', style: const TextStyle(color: AppTheme.textTertiary, fontSize: 12)),
              const SizedBox(height: 20),
              SizedBox(
                height: 200,
                child: LineChart(LineChartData(
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    getDrawingHorizontalLine: (_) => const FlLine(color: Color(0x1AFFFFFF), strokeWidth: 1),
                  ),
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 28,
                      getTitlesWidget: (v, _) => v.toInt() % 3 == 0
                        ? Text('D${v.toInt() + 1}', style: const TextStyle(color: AppTheme.textTertiary, fontSize: 10))
                        : const SizedBox())),
                    leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 40,
                      getTitlesWidget: (v, _) => Text(v.toInt().toString(), style: const TextStyle(color: AppTheme.textTertiary, fontSize: 10)))),
                  ),
                  borderData: FlBorderData(show: false),
                  lineBarsData: [
                    LineChartBarData(
                      spots: spots,
                      isCurved: true,
                      color: AppTheme.primary,
                      barWidth: 2.5,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        gradient: LinearGradient(
                          colors: [AppTheme.primary.withOpacity(0.3), AppTheme.primary.withOpacity(0)],
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                        ),
                      ),
                    ),
                  ],
                )),
              ),
            ],
          ),
        ).animate().fadeIn(),
      ],
    );
  }
}
