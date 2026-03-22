import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'https://responses-michigan-buy-august.trycloudflare.com/api/';
  String? _token;
  String? _role;
  String? _userId;
  String? _userName;
  String? _userEmail;

  // Singleton pattern
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  void setToken(String token) => _token = token;
  void setRole(String role) => _role = role;
  String? get userId => _userId;
  String? get userName => _userName;
  String? get userEmail => _userEmail;

  void logout() {
    _token = null;
    _role = null;
    _userId = null;
    _userName = null;
    _userEmail = null;
  }

  bool get isCoach => _role == 'ADMIN';

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (_token != null) 'Authorization': 'Bearer $_token',
  };

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('${baseUrl}auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    
    // Log for debugging if it's not JSON
    if (!response.headers['content-type']!.contains('application/json')) {
      return {'error': 'El servidor no respondió con JSON. Verifica la ruta.'};
    }
    
    final data = jsonDecode(response.body);
    if (data.containsKey('token')) {
      _token = data['token'];
    }
    if (data.containsKey('role')) {
      _role = data['role'];
    }
    if (data.containsKey('id')) {
      _userId = data['id'];
    }
    if (data.containsKey('name')) {
      _userName = data['name'];
    }
    if (data.containsKey('email')) {
      _userEmail = data['email'];
    }
    return data;
  }

  Future<Map<String, dynamic>> register(String name, String email, String password) async {
    final response = await http.post(
      Uri.parse('${baseUrl}auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'name': name, 'email': email, 'password': password}),
    );
    if (!response.headers['content-type']!.contains('application/json')) {
      return {'error': 'Error de servidor (HTML)'};
    }
    final data = jsonDecode(response.body);
    if (data.containsKey('id')) {
      _userId = data['id'];
    }
    return data;
  }

  Future<List<dynamic>> getDietPlan({String? userId}) async {
    final uri = userId != null ? Uri.parse('${baseUrl}client/my_plan?user_id=$userId') : Uri.parse('${baseUrl}client/my_plan');
    final response = await http.get(uri, headers: _headers);
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Error al cargar plan nutricional');
  }

  Future<List<dynamic>> getWorkoutPlan({String? userId}) async {
    final uri = userId != null ? Uri.parse('${baseUrl}client/my_workout?user_id=$userId') : Uri.parse('${baseUrl}client/my_workout');
    final response = await http.get(uri, headers: _headers);
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Error al cargar rutina');
  }

  Future<List<dynamic>> getChatMessages() async {
    final response = await http.get(Uri.parse('${baseUrl}chat'), headers: _headers);
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  }

  Future<List<dynamic>> getAllUsers() async {
    final response = await http.get(Uri.parse('${baseUrl}admin/users'), headers: _headers);
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  }

  Future<Map<String, dynamic>> sendChatMessage(String message) async {
    final response = await http.post(
      Uri.parse('${baseUrl}chat'),
      headers: _headers,
      body: jsonEncode({'message': message}),
    );
    return jsonDecode(response.body);
  }

  // --- Admin Methods ---
  Future<List<dynamic>> getAdminFoods() async {
    final response = await http.get(Uri.parse('${baseUrl}admin/foods'), headers: _headers);
    return response.statusCode == 200 ? jsonDecode(response.body) : [];
  }

  Future<Map<String, dynamic>> assignFood(String userId, int foodId, String dayName, String mealName, double grams) async {
    final response = await http.post(
      Uri.parse('${baseUrl}admin/assign_food'),
      headers: _headers,
      body: jsonEncode({
        'user_id': userId,
        'food_id': foodId,
        'day_name': dayName,
        'meal_name': mealName,
        'grams': grams,
      }),
    );
    return jsonDecode(response.body);
  }

  Future<List<dynamic>> getAdminExercises() async {
    final response = await http.get(Uri.parse('${baseUrl}admin/exercises'), headers: _headers);
    return response.statusCode == 200 ? jsonDecode(response.body) : [];
  }

  Future<Map<String, dynamic>> assignExercise(String userId, int exerciseId, String day, int sets, String reps, {String rest = '', String targetMuscles = ''}) async {
    final response = await http.post(
      Uri.parse('${baseUrl}admin/assign_exercise'),
      headers: _headers,
      body: jsonEncode({
        'user_id': userId,
        'exercise_id': exerciseId,
        'day_of_week': day,
        'target_muscles': targetMuscles,
        'sets': sets,
        'reps': reps,
        'rest': rest,
      }),
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> removeFood(int id) async {
    final response = await http.delete(Uri.parse('${baseUrl}admin/remove_food/$id'), headers: _headers);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> removeExercise(int id) async {
    final response = await http.delete(Uri.parse('${baseUrl}admin/remove_exercise/$id'), headers: _headers);
    return jsonDecode(response.body);
  }

  // --- Measurements ---
  Future<Map<String, dynamic>> logMeasurement(Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('${baseUrl}measurements'),
      headers: _headers,
      body: jsonEncode(data),
    );
    return jsonDecode(response.body);
  }

  Future<List<dynamic>> getMeasurements(String userId) async {
    final response = await http.get(
      Uri.parse('${baseUrl}measurements?user_id=$userId'),
      headers: _headers,
    );
    return response.statusCode == 200 ? jsonDecode(response.body) : [];
  }

  // --- Social Media Agent ---
  Future<List<dynamic>> getSocialPosts() async {
    final response = await http.get(Uri.parse('${baseUrl}admin/social_posts'), headers: _headers);
    return response.statusCode == 200 ? jsonDecode(response.body) : [];
  }

  Future<void> approveSocialPost(int id) async {
    final response = await http.post(Uri.parse('${baseUrl}admin/social_posts/approve/$id'), headers: _headers);
    if (response.statusCode != 200) throw Exception('No se pudo aprobar el post');
  }

  Future<void> rejectSocialPost(int id) async {
    final response = await http.post(Uri.parse('${baseUrl}admin/social_posts/reject/$id'), headers: _headers);
    if (response.statusCode != 200) throw Exception('No se pudo rechazar el post');
  }

  Future<void> generateSocialProposal() async {
    final response = await http.post(Uri.parse('${baseUrl}admin/social_posts/generate'), headers: _headers);
    if (response.statusCode != 200) throw Exception('No se pudo generar la propuesta');
  }
}
