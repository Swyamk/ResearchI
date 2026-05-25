import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/screens/login_screen.dart';
import '../features/auth/screens/register_screen.dart';
import '../features/dashboard/screens/dashboard_screen.dart';
import '../features/meals/screens/camera_screen.dart';
import '../features/meals/screens/meal_history_screen.dart';
import '../features/ai_coach/screens/ai_coach_screen.dart';
import '../features/analytics/screens/analytics_screen.dart';
import '../features/profile/screens/profile_screen.dart';
import '../features/shell/app_shell.dart';

final _storage = const FlutterSecureStorage();

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/dashboard',
    redirect: (context, state) async {
      final token = await _storage.read(key: 'access_token');
      final isAuth = token != null;
      final isAuthRoute = state.matchedLocation.startsWith('/auth');

      if (!isAuth && !isAuthRoute) return '/auth/login';
      if (isAuth && isAuthRoute) return '/dashboard';
      return null;
    },
    routes: [
      // Auth routes
      GoRoute(path: '/auth/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/auth/register', builder: (_, __) => const RegisterScreen()),

      // Main app shell with bottom nav
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          GoRoute(path: '/dashboard', builder: (_, __) => const DashboardScreen()),
          GoRoute(path: '/meals', builder: (_, __) => const MealHistoryScreen()),
          GoRoute(path: '/ai-coach', builder: (_, __) => const AiCoachScreen()),
          GoRoute(path: '/analytics', builder: (_, __) => const AnalyticsScreen()),
          GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
        ],
      ),

      // Camera (full screen, no bottom nav)
      GoRoute(path: '/camera', builder: (_, __) => const CameraScreen()),
    ],
  );
});
