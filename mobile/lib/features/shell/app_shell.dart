import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../core/theme/app_theme.dart';

class AppShell extends StatelessWidget {
  final Widget child;
  const AppShell({super.key, required this.child});

  static const _tabs = [
    (icon: Icons.dashboard_rounded, label: 'Home', route: '/dashboard'),
    (icon: Icons.restaurant_menu_rounded, label: 'Meals', route: '/meals'),
    (icon: Icons.psychology_rounded, label: 'AI Coach', route: '/ai-coach'),
    (icon: Icons.bar_chart_rounded, label: 'Analytics', route: '/analytics'),
    (icon: Icons.person_rounded, label: 'Profile', route: '/profile'),
  ];

  int _locationIndex(BuildContext context) {
    final loc = GoRouterState.of(context).matchedLocation;
    for (int i = 0; i < _tabs.length; i++) {
      if (loc.startsWith(_tabs[i].route)) return i;
    }
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    final idx = _locationIndex(context);
    return Scaffold(
      body: child,
      // FAB for camera
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/camera'),
        backgroundColor: AppTheme.primary,
        elevation: 4,
        child: const Icon(Icons.camera_alt_rounded, color: Colors.white),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
      bottomNavigationBar: BottomAppBar(
        color: AppTheme.surface,
        shape: const CircularNotchedRectangle(),
        notchMargin: 8,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            for (int i = 0; i < _tabs.length; i++) ...[
              if (i == 2) const SizedBox(width: 48),
              _NavItem(
                icon: _tabs[i].icon,
                label: _tabs[i].label,
                selected: idx == i,
                onTap: () => context.go(_tabs[i].route),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const _NavItem({required this.icon, required this.label, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 200),
          child: Column(
            key: ValueKey(selected),
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: selected ? AppTheme.primary : AppTheme.textTertiary, size: 22),
              const SizedBox(height: 2),
              Text(label, style: TextStyle(
                fontSize: 10, color: selected ? AppTheme.primary : AppTheme.textTertiary,
                fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
              )),
            ],
          ),
        ),
      ),
    );
  }
}
