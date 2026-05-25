import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/api/api_client.dart';

class MealHistoryScreen extends ConsumerStatefulWidget {
  const MealHistoryScreen({super.key});
  @override
  ConsumerState<MealHistoryScreen> createState() => _MealHistoryScreenState();
}

class _MealHistoryScreenState extends ConsumerState<MealHistoryScreen> {
  List<dynamic> _meals = [];
  bool _loading = true;
  int _page = 1;
  bool _hasMore = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load({bool refresh = false}) async {
    if (refresh) { _page = 1; _meals = []; _hasMore = true; }
    if (!_hasMore) return;
    try {
      final data = await ref.read(apiClientProvider).getMeals(page: _page);
      final newMeals = data['meals'] as List? ?? [];
      setState(() {
        _meals.addAll(newMeals);
        _hasMore = data['has_next'] ?? false;
        _loading = false;
        _page++;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  static const _mealColors = {
    'breakfast': Color(0xFFF59E0B), 'lunch': Color(0xFF10B981),
    'dinner': Color(0xFF6366F1), 'snack': Color(0xFFEC4899),
    'pre_workout': Color(0xFF8B5CF6), 'post_workout': Color(0xFF06B6D4),
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('Meal History'),
        backgroundColor: AppTheme.background,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => _load(refresh: true),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
          : _meals.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.restaurant_menu_rounded, size: 56, color: AppTheme.textTertiary),
                      const SizedBox(height: 16),
                      const Text('No meals logged yet', style: TextStyle(color: AppTheme.textSecondary, fontSize: 16)),
                      const SizedBox(height: 8),
                      const Text('Use the camera button to log your first meal', style: TextStyle(color: AppTheme.textTertiary, fontSize: 13)),
                    ],
                  ),
                )
              : RefreshIndicator(
                  color: AppTheme.primary,
                  onRefresh: () => _load(refresh: true),
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                    itemCount: _meals.length + (_hasMore ? 1 : 0),
                    itemBuilder: (ctx, i) {
                      if (i == _meals.length) {
                        _load();
                        return const Padding(
                          padding: EdgeInsets.all(16),
                          child: Center(child: CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 2)),
                        );
                      }
                      final meal = _meals[i];
                      final mealType = meal['meal_type'] ?? 'lunch';
                      final color = _mealColors[mealType] ?? AppTheme.primary;
                      final time = DateTime.tryParse(meal['meal_time'] ?? '');
                      final items = (meal['food_items'] as List?) ?? [];

                      return Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: AppTheme.glassCard,
                        child: ExpansionTile(
                          tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                          leading: Container(
                            width: 44, height: 44,
                            decoration: BoxDecoration(
                              color: color.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: color.withOpacity(0.3)),
                            ),
                            child: Icon(Icons.restaurant_rounded, color: color, size: 20),
                          ),
                          title: Text(mealType.replaceAll('_', ' ').toUpperCase(),
                            style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 12, letterSpacing: 0.5)),
                          subtitle: time != null
                            ? Text(DateFormat('MMM d · h:mm a').format(time.toLocal()),
                                style: const TextStyle(color: AppTheme.textTertiary, fontSize: 12))
                            : null,
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text('${(meal['total_calories'] ?? 0).toStringAsFixed(0)} kcal',
                                style: const TextStyle(color: AppTheme.calorieColor, fontWeight: FontWeight.w700, fontSize: 15)),
                              Text('${items.length} items', style: const TextStyle(color: AppTheme.textTertiary, fontSize: 11)),
                            ],
                          ),
                          children: [
                            const Divider(height: 1, color: Color(0x1AFFFFFF)),
                            for (final item in items)
                              ListTile(
                                dense: true,
                                title: Text(item['name']?.toString() ?? '',
                                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13)),
                                subtitle: Text('${item['portion_size_g']?.toStringAsFixed(0) ?? 0}g',
                                  style: const TextStyle(color: AppTheme.textTertiary, fontSize: 11)),
                                trailing: Text('${item['calories']?.toStringAsFixed(0) ?? 0} kcal',
                                  style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                              ),
                          ],
                        ),
                      ).animate().fadeIn(delay: (i * 50).ms).slideY(begin: 0.05);
                    },
                  ),
                ),
    );
  }
}
