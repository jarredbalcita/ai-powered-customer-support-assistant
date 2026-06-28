import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  String _message = 'Loading...';
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchMessage();
  }

  Future<void> _fetchMessage() async {
    final baseUrl = Platform.isAndroid
        ? 'http://10.0.2.2:8000'
        : 'http://127.0.0.1:8000';
    final uri = Uri.parse('$baseUrl/api/message');

    try {
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        setState(() {
          _message = body['message'] as String;
          _isLoading = false;
        });
      } else {
        setState(() {
          _message = 'Request failed with status: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (error) {
      setState(() {
        _message = 'Unable to reach the backend: $error';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI Support Assistant',
      home: Scaffold(
        appBar: AppBar(
          title: const Text('AI Support Assistant'),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                'Frontend connected to FastAPI backend',
                style: TextStyle(fontSize: 20),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _fetchMessage,
                child: const Text('Refresh message'),
              ),
              const SizedBox(height: 16),
              Text(
                _isLoading ? 'Loading...' : _message,
                style: const TextStyle(fontSize: 16),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
