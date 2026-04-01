import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'https://mt-fitness-pro.onrender.com/api/';
  static const String uploadsUrl = 'https://mt-fitness-pro.onrender.com/uploads/';
  
  String? _token;
  String? _role;
  String? _userId;
  String? _userName;
  String? _userEmail;
  String? _surname;
  int? _age;
  double? _height;
  double? _currentWeight;
  String? _objective;
  int? _daysLeft;
  String? _profileImage;
  double? _biceps;
  double? _thigh;
  double? _hip;
  double? _waist;

  // Singleton pattern
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  void setToken(String token) => _token = token;
  void setRole(String role) => _role = role;
  String? get userId => _userId;
  String? get userName => _userName;
  String? get userEmail => _userEmail;
  String? get surname => _surname;
  int? get age => _age;
  double? get height => _height;
  double? get currentWeight => _currentWeight;
  String? get objective => _objective;
  int? get daysLeft => _daysLeft;
  String? get profileImage => _profileImage;
  double? get biceps => _biceps;
  double? get thigh => _thigh;
  double? get hip => _hip;
  double? get waist => _waist;

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
    
    if (!response.headers['content-type']!.contains('application/json')) {
      return {'error': 'El servidor no respondió con JSON.'};
    }
    
    final data = jsonDecode(response.body);
    if (data.containsKey('token')) _token = data['token'];
    if (data.containsKey('role')) _role = data['role'];
    if (data.containsKey('id')) _userId = data['id'];
    if (data.containsKey('name')) _userName = data['name'];
    if (data.containsKey('surname')) _surname = data['surname'];
    if (data.containsKey('email')) _userEmail = data['email'];
    if (data.containsKey('age')) _age = data['age'];
    if (data.containsKey('height')) _height = data['height']?.toDouble();
    if (data.containsKey('current_weight')) _currentWeight = data['current_weight']?.toDouble();
    if (data.containsKey('objective')) _objective = data['objective'];
    if (data.containsKey('days_left')) _daysLeft = data['days_left'];
    if (data.containsKey('profile_image')) _profileImage = data['profile_image'];
    if (data.containsKey('biceps')) _biceps = data['biceps']?.toDouble();
    if (data.containsKey('thigh')) _thigh = data['thigh']?.toDouble();
    if (data.containsKey('hip')) _hip = data['hip']?.toDouble();
    if (data.containsKey('waist')) _waist = data['waist']?.toDouble();
    
    return data;
  }

  Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('${baseUrl}auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );
    return jsonDecode(response.body);
  }

  Future<List<dynamic>> getDietPlan({String? userId}) async {
    final query = userId != null ? '?user_id=$userId' : '';
    final response = await http.get(Uri.parse('${baseUrl}client/my_diet$query'), headers: _headers);
    return response.statusCode == 200 ? jsonDecode(response.body) : [];
  }

  Future<List<dynamic>> getWorkoutPlan({String? userId}) async {
    final query = userId != null ? '?user_id=$userId' : '';
    final response = await http.get(Uri.parse('${baseUrl}client/my_workout$query'), headers: _headers);
    return response.statusCode == 200 ? jsonDecode(response.body) : [];
  }

  Future<List<dynamic>> getChatMessages() async {
    final response = await http.get(Uri.parse('${baseUrl}chat'), headers: _headers);
    return response.statusCode == 200 ? jsonDecode(response.body) : [];
  }

  Future<List<dynamic>> getAllUsers() async {
    final response = await http.get(Uri.parse('${baseUrl}admin/users'), headers: _headers);
    return response.statusCode == 200 ? jsonDecode(response.body) : [];
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

  Future<void> addToExerciseCatalog(String name, String muscleGroup) async {
    await http.post(
      Uri.parse('${baseUrl}admin/add_exercise'),
      headers: _headers,
      body: jsonEncode({'name': name, 'muscle_group': muscleGroup}),
    );
  }

  Future<void> addToFoodCatalog(Map<String, dynamic> data) async {
    await http.post(Uri.parse('${baseUrl}admin/add_food'), headers: _headers, body: jsonEncode(data));
  }

  Future<Map<String, dynamic>> assignExercise(String userId, int exerciseId, String day, int sets, String reps, {String rest = '', String targetMuscles = '', String setType = 'NORMAL', int? combinedWith}) async {
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
        'set_type': setType,
        'combined_with': combinedWith,
      }),
    );
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> removeFood(int id) async {
    final response = await http.delete(Uri.parse('${baseUrl}admin/remove_food/$id'), headers: _headers);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> deleteCatalogExercise(int id) async {
    final response = await http.delete(Uri.parse('${baseUrl}admin/catalog/exercise/$id'), headers: _headers);
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> removeExercise(int id) async {
    final response = await http.delete(Uri.parse('${baseUrl}admin/remove_exercise/$id'), headers: _headers);
    return jsonDecode(response.body);
  }

  // --- Admin Coach Actions ---
  Future<void> approveUser(String userId) async {
    final response = await http.post(Uri.parse('${baseUrl}admin/approve/$userId'), headers: _headers);
    if (response.statusCode != 200) throw Exception('No se pudo aprobar al usuario');
  }

  Future<void> addSubscription(String userId, int days) async {
    final response = await http.post(
      Uri.parse('${baseUrl}admin/add_subscription/$userId'),
      headers: _headers,
      body: jsonEncode({'days': days}),
    );
    if (response.statusCode != 200) throw Exception('No se pudo añadir la suscripción');
  }

  // --- Measurements ---
  Future<Map<String, dynamic>> logMeasurement(Map<String, dynamic> data) async {
    final response = await http.post(Uri.parse('${baseUrl}measurements'), headers: _headers, body: jsonEncode(data));
    return jsonDecode(response.body);
  }

  Future<List<dynamic>> getMeasurements(String userId) async {
    final response = await http.get(Uri.parse('${baseUrl}measurements?user_id=$userId'), headers: _headers);
    return response.statusCode == 200 ? jsonDecode(response.body) : [];
  }

  // --- Social Media Agent ---
  Future<List<dynamic>> getSocialPosts() async {
    final response = await http.get(Uri.parse('${baseUrl}admin/social_posts'), headers: _headers);
    return response.statusCode == 200 ? jsonDecode(response.body) : [];
  }

  Future<void> approveSocialPost(int id) async {
    await http.post(Uri.parse('${baseUrl}admin/social_posts/approve/$id'), headers: _headers);
  }

  Future<void> rejectSocialPost(int id) async {
    await http.post(Uri.parse('${baseUrl}admin/social_posts/reject/$id'), headers: _headers);
  }

  Future<void> generateSocialProposal() async {
    await http.post(Uri.parse('${baseUrl}admin/social_posts/generate'), headers: _headers);
  }

  // --- Profile update with Image support ---
  Future<void> updateProfile(Map<String, dynamic> data, {String? imagePath}) async {
    final url = Uri.parse('${baseUrl}profile/update');
    
    if (imagePath != null) {
      final request = http.MultipartRequest('POST', url);
      request.headers.addAll({
        if (_token != null) 'Authorization': 'Bearer $_token',
      });
      
      request.fields['name'] = data['name'] ?? '';
      request.fields['surname'] = data['surname'] ?? '';
      request.fields['age'] = (data['age'] ?? '').toString();
      request.fields['height'] = (data['height'] ?? '').toString();
      request.fields['current_weight'] = (data['current_weight'] ?? '').toString();
      request.fields['objective'] = data['objective'] ?? '';
      request.fields['biceps'] = (data['biceps'] ?? '').toString();
      request.fields['thigh'] = (data['thigh'] ?? '').toString();
      request.fields['hip'] = (data['hip'] ?? '').toString();
      request.fields['waist'] = (data['waist'] ?? '').toString();
      
      request.files.add(await http.MultipartFile.fromPath('profile_image', imagePath));
      
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      if (response.statusCode == 200) {
        final resData = jsonDecode(response.body);
        _profileImage = resData['profile_image'];
      } else {
        throw Exception('Error al actualizar con imagen: ${response.body}');
      }
    } else {
      final response = await http.post(url, headers: _headers, body: jsonEncode(data));
      if (response.statusCode != 200) throw Exception('Error al actualizar perfil');
    }
    
    // Sync local state
    _userName = data['name'];
    _surname = data['surname'];
    _age = data['age'];
    _height = data['height']?.toDouble();
    _currentWeight = data['current_weight']?.toDouble();
    _objective = data['objective'];
    _biceps = data['biceps']?.toDouble();
    _thigh = data['thigh']?.toDouble();
    _hip = data['hip']?.toDouble();
    _waist = data['waist']?.toDouble();
  }

  Future<void> submitReport(String weight, String? photoFront, String? photoSide, String? photoBack, {String? biceps, String? thigh, String? hip, String? waist}) async {
    final request = http.MultipartRequest('POST', Uri.parse('${baseUrl}reports/submit'));
    request.headers.addAll({
      if (_token != null) 'Authorization': 'Bearer $_token',
    });
    request.fields['weight'] = weight;
    request.fields['biceps'] = biceps ?? '';
    request.fields['thigh'] = thigh ?? '';
    request.fields['hip'] = hip ?? '';
    request.fields['waist'] = waist ?? '';
    
    if (photoFront != null) request.files.add(await http.MultipartFile.fromPath('photo_front', photoFront));
    if (photoSide != null) request.files.add(await http.MultipartFile.fromPath('photo_side', photoSide));
    if (photoBack != null) request.files.add(await http.MultipartFile.fromPath('photo_back', photoBack));
    
    final streamedResponse = await request.send();
    if (streamedResponse.statusCode != 200) {
      final response = await http.Response.fromStream(streamedResponse);
      throw Exception('Error al enviar el reporte: ${response.body}');
    }
  }

  Future<void> updateExercise(int assignmentId, Map<String, dynamic> data) async {
    await http.post(
      Uri.parse('${baseUrl}admin/update_exercise/$assignmentId'),
      headers: _headers,
      body: jsonEncode(data),
    );
  }

  Future<void> updateFood(int assignmentId, Map<String, dynamic> data) async {
    await http.post(
      Uri.parse('${baseUrl}admin/update_food/$assignmentId'),
      headers: _headers,
      body: jsonEncode(data),
    );
  }

  Future<List<dynamic>> getReportHistory(String userId) async {
    final response = await http.get(Uri.parse('${baseUrl}reports/history/$userId'), headers: _headers);
    return response.statusCode == 200 ? jsonDecode(response.body) : [];
  }
}
