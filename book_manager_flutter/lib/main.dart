import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const BookManagerApp());
}

class BookManagerApp extends StatelessWidget {
  const BookManagerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Book Manager',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
