import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Support Assistant',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(colorSchemeSeed: Colors.blue, useMaterial3: true),
        home: const ChatScreen(),
      );
}

// ─── Chat screen ─────────────────────────────────────────────────────────────

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final List<Widget> _messages = [];
  bool _loading = false;

  static const String _backendUrl = 'http://localhost:8000/chat';

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _loading) return;

    setState(() {
      _messages.add(_bubble(text, isUser: true));
      _controller.clear();
      _loading = true;
    });
    _scrollToBottom();

    try {
      final res = await http.post(
        Uri.parse(_backendUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': text}),
      );
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      setState(() {
        _messages.add(_render(data));
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _messages.add(_bubble('Error: unable to reach server.', isUser: false));
        _loading = false;
      });
    }
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Widget _render(Map<String, dynamic> r) {
    final data = (r['data'] as Map<String, dynamic>?) ?? {};
    final message = (r['message'] as String?) ?? '';
    switch (r['ui_type']) {
      case 'hotel_page':
        return HotelWidget(data: data);
      case 'flight_page':
        return FlightWidget(data: data);
      case 'tracking_page':
        return TrackingWidget(data: data, message: message);
      case 'refund_page':
        return RefundWidget(data: data, message: message);
      case 'complaint_page':
        return ComplaintWidget(data: data, message: message);
      case 'escalation_page':
        return EscalationWidget(data: data, message: message);
      default:
        return _bubble(message, isUser: false);
    }
  }

  Widget _bubble(String text, {required bool isUser}) => Align(
        alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
          constraints: const BoxConstraints(maxWidth: 320),
          decoration: BoxDecoration(
            color: isUser ? Colors.blue.shade100 : Colors.grey.shade200,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Text(text),
        ),
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Support Assistant'), centerTitle: true),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(8),
              itemCount: _messages.length,
              itemBuilder: (_, i) => _messages[i],
            ),
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Row(
                children: [
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  SizedBox(width: 8),
                  Text('Thinking...', style: TextStyle(color: Colors.grey)),
                ],
              ),
            ),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    enabled: !_loading,
                    decoration: const InputDecoration(
                      hintText: 'Type a message...',
                      border: OutlineInputBorder(),
                      contentPadding:
                          EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    ),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  icon: const Icon(Icons.send),
                  onPressed: _loading ? null : _send,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Shared helpers ──────────────────────────────────────────────────────────

Widget _infoRow(String label, String value) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
        ],
      ),
    );

// ─── Widgets ─────────────────────────────────────────────────────────────────

class HotelWidget extends StatelessWidget {
  final Map<String, dynamic> data;
  const HotelWidget({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final hotels = (data['hotels'] as List?) ?? [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(8, 8, 8, 4),
          child: Text('Available Hotels',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        ),
        ...hotels.map<Widget>((h) {
          final hotel = h as Map<String, dynamic>;
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
            child: ListTile(
              leading: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Container(
                  width: 50,
                  height: 50,
                  color: Colors.blue.shade50,
                  child: const Icon(Icons.hotel, color: Colors.blue, size: 28),
                ),
              ),
              title: Text(hotel['name']?.toString() ?? '',
                  style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(hotel['location']?.toString() ?? ''),
                  Row(children: [
                    const Icon(Icons.star, size: 14, color: Colors.amber),
                    Text(' ${hotel["rating"]}',
                        style: const TextStyle(fontSize: 12)),
                  ]),
                ],
              ),
              trailing: Text(
                hotel['price']?.toString() ?? '',
                style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: Colors.green),
              ),
              isThreeLine: true,
            ),
          );
        }),
      ],
    );
  }
}

class FlightWidget extends StatelessWidget {
  final Map<String, dynamic> data;
  const FlightWidget({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final flights = (data['flights'] as List?) ?? [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.fromLTRB(8, 8, 8, 4),
          child: Text('Available Flights',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        ),
        ...flights.map<Widget>((f) {
          final flight = f as Map<String, dynamic>;
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
            child: ListTile(
              leading: const Icon(Icons.flight_takeoff,
                  color: Colors.blue, size: 36),
              title: Text(flight['airline']?.toString() ?? '',
                  style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text(
                  '${flight["from"]} → ${flight["to"]}  • Dep: ${flight["departure"]} → • Arr: ${flight["arrival"]}'),
              trailing: Text(
                flight['price']?.toString() ?? '',
                style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: Colors.green),
              ),
            ),
          );
        }),
      ],
    );
  }
}

class TrackingWidget extends StatelessWidget {
  final Map<String, dynamic> data;
  final String message;
  const TrackingWidget({super.key, required this.data, required this.message});

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                const Icon(Icons.local_shipping, color: Colors.blue),
                const SizedBox(width: 8),
                Text(message,
                    style: const TextStyle(fontWeight: FontWeight.bold)),
              ]),
              const Divider(),
              _infoRow('Order ID', data['order_id']?.toString() ?? ''),
              _infoRow('Status', data['status']?.toString() ?? ''),
              _infoRow('ETA', data['eta']?.toString() ?? ''),
              _infoRow('Carrier', data['carrier']?.toString() ?? ''),
              const SizedBox(height: 2),
              _infoRow('Last Location', data['last_location']?.toString() ?? ''),
            ],
          ),
        ),
      );
}

class RefundWidget extends StatelessWidget {
  final Map<String, dynamic> data;
  final String message;
  const RefundWidget({super.key, required this.data, required this.message});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              const Icon(Icons.currency_exchange, color: Colors.green),
              const SizedBox(width: 8),
              Text(message,
                  style: const TextStyle(fontWeight: FontWeight.bold)),
            ]),
            const Divider(),
            _infoRow('Refund ID', data['refund_id']?.toString() ?? ''),
            _infoRow('Amount', data['amount']?.toString() ?? ''),
            _infoRow('Status', data['status']?.toString() ?? ''),
            _infoRow('Timeline', data['estimated_days']?.toString() ?? ''),
          ],
        ),
      ),
    );
  }
}

class ComplaintWidget extends StatelessWidget {
  final Map<String, dynamic> data;
  final String message;
  const ComplaintWidget({super.key, required this.data, required this.message});

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                const Icon(Icons.report_problem, color: Colors.orange),
                const SizedBox(width: 8),
                Flexible(
                    child: Text(message,
                        style: const TextStyle(fontWeight: FontWeight.bold))),
              ]),
              const Divider(),
              _infoRow('Ticket ID', data['ticket_id']?.toString() ?? ''),
              _infoRow('Status', data['status']?.toString() ?? ''),
              _infoRow('Priority', data['priority']?.toString() ?? ''),
              if (data['note'] != null) ...[
                const SizedBox(height: 8),
                Text(data['note'].toString(),
                    style: const TextStyle(color: Colors.grey, fontSize: 12)),
              ],
            ],
          ),
        ),
      );
}

class EscalationWidget extends StatelessWidget {
  final Map<String, dynamic> data;
  final String message;
  const EscalationWidget(
      {super.key, required this.data, required this.message});

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                const Icon(Icons.support_agent, color: Colors.red),
                const SizedBox(width: 8),
                Flexible(
                    child: Text(message,
                        style: const TextStyle(fontWeight: FontWeight.bold))),
              ]),
              const Divider(),
              _infoRow('Ticket ID', data['ticket_id']?.toString() ?? ''),
              _infoRow('Assigned To', data['assigned_to']?.toString() ?? ''),
              _infoRow('Response Time',
                  data['expected_response']?.toString() ?? ''),
            ],
          ),
        ),
      );
}
