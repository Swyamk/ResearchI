import 'dart:io';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/api/api_client.dart';

class CameraScreen extends ConsumerStatefulWidget {
  const CameraScreen({super.key});
  @override
  ConsumerState<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends ConsumerState<CameraScreen> {
  CameraController? _ctrl;
  List<CameraDescription> _cameras = [];
  bool _ready = false;
  bool _analyzing = false;
  Map<String, dynamic>? _result;
  String _mealType = 'lunch';
  File? _capturedImage;

  final _mealTypes = ['breakfast', 'lunch', 'dinner', 'snack', 'pre_workout', 'post_workout'];

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras.isEmpty) return;
      _ctrl = CameraController(_cameras.first, ResolutionPreset.high, enableAudio: false);
      await _ctrl!.initialize();
      if (mounted) setState(() => _ready = true);
    } catch (_) {}
  }

  Future<void> _capture() async {
    if (_ctrl == null || !_ready) return;
    final file = await _ctrl!.takePicture();
    setState(() { _capturedImage = File(file.path); _result = null; });
    await _analyze(file.path);
  }

  Future<void> _pickFromGallery() async {
    final img = await ImagePicker().pickImage(source: ImageSource.gallery, imageQuality: 85);
    if (img == null) return;
    setState(() { _capturedImage = File(img.path); _result = null; });
    await _analyze(img.path);
  }

  Future<void> _analyze(String path) async {
    setState(() => _analyzing = true);
    try {
      final data = await ref.read(apiClientProvider).analyzeMeal(path, _mealType);
      if (mounted) setState(() { _result = data; _analyzing = false; });
    } catch (_) {
      if (mounted) setState(() => _analyzing = false);
    }
  }

  @override
  void dispose() {
    _ctrl?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Camera preview or captured image
          if (_capturedImage != null)
            Positioned.fill(child: Image.file(_capturedImage!, fit: BoxFit.cover))
          else if (_ready && _ctrl != null)
            Positioned.fill(child: CameraPreview(_ctrl!))
          else
            const Center(child: CircularProgressIndicator(color: AppTheme.primary)),

          // Top bar
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () => context.pop(),
                    child: Container(
                      width: 40, height: 40,
                      decoration: BoxDecoration(color: Colors.black45, borderRadius: BorderRadius.circular(12)),
                      child: const Icon(Icons.close, color: Colors.white),
                    ),
                  ),
                  const Spacer(),
                  // Meal type selector
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(20)),
                    child: DropdownButton<String>(
                      value: _mealType,
                      dropdownColor: AppTheme.surface,
                      style: const TextStyle(color: Colors.white, fontSize: 13),
                      underline: const SizedBox(),
                      icon: const Icon(Icons.keyboard_arrow_down, color: Colors.white, size: 18),
                      items: _mealTypes.map((t) => DropdownMenuItem(
                        value: t,
                        child: Text(t.replaceAll('_', ' '), style: const TextStyle(fontSize: 13)),
                      )).toList(),
                      onChanged: (v) => setState(() => _mealType = v!),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Analysis result overlay
          if (_result != null)
            Positioned(
              left: 0, right: 0, bottom: 0,
              child: _ResultPanel(result: _result!).animate().slideY(begin: 1, end: 0),
            )
          else if (_analyzing)
            const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(color: AppTheme.primary, strokeWidth: 3),
                  SizedBox(height: 16),
                  Text('Analyzing meal...', style: TextStyle(color: Colors.white, fontSize: 14)),
                  SizedBox(height: 4),
                  Text('YOLOv8 → SAM2 → EfficientNetV2', style: TextStyle(color: Colors.white54, fontSize: 11)),
                ],
              ),
            )
          else if (_capturedImage == null)
            // Camera controls
            Positioned(
              left: 0, right: 0, bottom: 40,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  IconButton(
                    icon: const Icon(Icons.photo_library_rounded, color: Colors.white, size: 32),
                    onPressed: _pickFromGallery,
                  ),
                  GestureDetector(
                    onTap: _capture,
                    child: Container(
                      width: 72, height: 72,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.white, width: 3),
                        gradient: AppTheme.primaryGradient,
                      ),
                      child: const Icon(Icons.camera_alt_rounded, color: Colors.white, size: 32),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.flip_camera_ios_rounded, color: Colors.white, size: 32),
                    onPressed: () async {
                      if (_cameras.length < 2) return;
                      final newCam = _ctrl!.description == _cameras.first ? _cameras.last : _cameras.first;
                      await _ctrl!.dispose();
                      _ctrl = CameraController(newCam, ResolutionPreset.high, enableAudio: false);
                      await _ctrl!.initialize();
                      if (mounted) setState(() {});
                    },
                  ),
                ],
              ),
            ),

          // Retake button when result shown
          if (_result != null || _capturedImage != null && !_analyzing)
            Positioned(
              top: 80, left: 16,
              child: GestureDetector(
                onTap: () => setState(() { _capturedImage = null; _result = null; }),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(color: Colors.black54, borderRadius: BorderRadius.circular(20)),
                  child: const Row(
                    children: [
                      Icon(Icons.refresh, color: Colors.white, size: 16),
                      SizedBox(width: 4),
                      Text('Retake', style: TextStyle(color: Colors.white, fontSize: 13)),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _ResultPanel extends StatelessWidget {
  final Map<String, dynamic> result;
  const _ResultPanel({required this.result});

  @override
  Widget build(BuildContext context) {
    final items = (result['detected_items'] as List?) ?? [];
    return Container(
      constraints: const BoxConstraints(maxHeight: 380),
      decoration: const BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          Container(width: 36, height: 4, margin: const EdgeInsets.symmetric(vertical: 12),
            decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              children: [
                const Icon(Icons.check_circle_rounded, color: AppTheme.primary, size: 18),
                const SizedBox(width: 8),
                const Text('Analysis Complete', style: TextStyle(color: AppTheme.primary, fontWeight: FontWeight.w600)),
                const Spacer(),
                Text('${result['total_calories']?.toStringAsFixed(0) ?? "0"} kcal',
                  style: const TextStyle(color: AppTheme.calorieColor, fontWeight: FontWeight.w700, fontSize: 18, fontFamily: 'Outfit')),
              ],
            ),
          ),
          const Divider(height: 24, color: Color(0x1AFFFFFF)),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
              itemCount: items.length,
              itemBuilder: (_, i) {
                final item = items[i];
                return ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 4),
                  leading: Container(
                    width: 40, height: 40,
                    decoration: BoxDecoration(gradient: AppTheme.primaryGradient, borderRadius: BorderRadius.circular(10)),
                    child: const Icon(Icons.restaurant_rounded, color: Colors.white, size: 18),
                  ),
                  title: Text(item['name']?.toString().replaceAll('_', ' ') ?? '',
                    style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600, fontSize: 14)),
                  subtitle: Text('${item['portion_g']?.toStringAsFixed(0) ?? 0}g · ${item['protein_g']?.toStringAsFixed(1) ?? 0}g protein',
                    style: const TextStyle(color: AppTheme.textTertiary, fontSize: 12)),
                  trailing: Text('${item['calories']?.toStringAsFixed(0) ?? 0} kcal',
                    style: const TextStyle(color: AppTheme.calorieColor, fontWeight: FontWeight.w600, fontSize: 13)),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
