import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

const _baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000/api/v1', // Android emulator → localhost
);

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

class ApiClient {
  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 60),
      sendTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.addAll([
      _AuthInterceptor(_storage),
      LogInterceptor(requestBody: false, responseBody: false),
    ]);
  }

  // ── Auth ────────────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> login(String email, String password) async {
    final res = await _dio.post('/auth/login',
      data: 'username=$email&password=$password',
      options: Options(headers: {'Content-Type': 'application/x-www-form-urlencoded'}),
    );
    return res.data;
  }

  Future<Map<String, dynamic>> register(String name, String email, String password) async {
    final res = await _dio.post('/auth/register',
      data: {'full_name': name, 'email': email, 'password': password},
    );
    return res.data;
  }

  // ── User ────────────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getMe() async {
    final res = await _dio.get('/users/me');
    return res.data;
  }

  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> data) async {
    final res = await _dio.put('/users/me/profile', data: data);
    return res.data;
  }

  // ── Meals ───────────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> analyzeMeal(
    String imagePath, String mealType,
  ) async {
    final formData = FormData.fromMap({
      'image': await MultipartFile.fromFile(imagePath, filename: 'meal.jpg'),
      'meal_type': mealType,
    });
    final res = await _dio.post('/meals/analyze', data: formData,
      options: Options(headers: {'Content-Type': 'multipart/form-data'}),
    );
    return res.data;
  }

  Future<Map<String, dynamic>> getMeals({int page = 1, int pageSize = 10}) async {
    final res = await _dio.get('/meals', queryParameters: {'page': page, 'page_size': pageSize});
    return res.data;
  }

  // ── Analytics ───────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getDashboard() async {
    final res = await _dio.get('/analytics/dashboard');
    return res.data;
  }

  Future<Map<String, dynamic>> getTodaySnapshot() async {
    final res = await _dio.get('/analytics/today');
    return res.data;
  }

  Future<Map<String, dynamic>> getWeeklySummary() async {
    final res = await _dio.get('/analytics/weekly');
    return res.data;
  }

  Future<Map<String, dynamic>> getNutritionTrend({int days = 30}) async {
    final res = await _dio.get('/analytics/trend', queryParameters: {'days': days});
    return res.data;
  }

  // ── AI Coach ─────────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> chatWithCoach(String message, String sessionId) async {
    final res = await _dio.post('/ai-coach/chat',
      data: {'message': message, 'session_id': sessionId},
    );
    return res.data;
  }

  Future<Map<String, dynamic>> getDailySummary() async {
    final res = await _dio.post('/ai-coach/summary/daily');
    return res.data;
  }

  // ── Recommendations ──────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getRecommendations({int limit = 5}) async {
    final res = await _dio.get('/recommendations/today', queryParameters: {'limit': limit});
    return res.data;
  }
}

class _AuthInterceptor extends Interceptor {
  final FlutterSecureStorage _storage;
  _AuthInterceptor(this._storage);

  @override
  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.response?.statusCode == 401) {
      _storage.delete(key: 'access_token');
      // Navigation handled by GoRouter redirect
    }
    handler.next(err);
  }
}
