# mcp-scotty Usage Examples

This document provides practical examples of using mcp-scotty with Claude Desktop.

## Basic Station Search

### Example 1: Find Vienna Main Station
```
User: Search for Vienna main station

Claude: [Uses search_stations tool]
Found stations:
- Wien Hauptbahnhof (ID: 1291501)
- Wien Meidling
- Wien Westbahnhof
```

### Example 2: Search for stations in Salzburg
```
User: Find train stations in Salzburg

Claude: [Uses search_stations tool]
Found stations:
- Salzburg Hauptbahnhof
- Salzburg Aiglhof
- Salzburg Aigen
- Salzburg Gnigl
- Salzburg Liefering
```

## Journey Planning

### Example 3: Simple journey query
```
User: What trains go from Vienna to Salzburg?

Claude: [Uses search_stations for both cities, then get_journeys]
Found 5 journeys from Wien Hauptbahnhof to Salzburg Hauptbahnhof:

Journey 1:
- Departure: 09:25 from Wien Hauptbahnhof
- Arrival: 12:03 at Salzburg Hauptbahnhof
- Duration: 2h 38min
- Transfers: 0
```

### Example 4: Journey with specific time
```
User: I need to go from Innsbruck to Graz tomorrow at 2 PM

Claude: [Uses get_journeys with date and time parameters]
Found journeys from Innsbruck Hauptbahnhof to Graz Hauptbahnhof on 2025-11-11 at 14:00:

Journey 1:
- Departure: 14:12 from Innsbruck Hauptbahnhof
- Arrival: 19:45 at Graz Hauptbahnhof
- Duration: 5h 33min
- Transfers: 1
```

### Example 5: Weekend trip planning
```
User: Plan a trip from Linz to Klagenfurt this Saturday morning

Claude: [Determines date, uses get_journeys]
Here are morning connections from Linz Hauptbahnhof to Klagenfurt Hauptbahnhof on Saturday, November 16:
[Shows journey options with times and transfers]
```

## Checking Departures

### Example 6: Current departures
```
User: What trains are leaving from Wien Hauptbahnhof right now?

Claude: [Uses get_departures]
Departures from Wien Hauptbahnhof:

- RJ 540 to Bregenz
  Departure: 10:25, Platform 7

- ICE 26 to Dortmund Hbf
  Departure: 10:30, Platform 3

- REX 2345 to St. Pölten
  Departure: 10:33, Platform 11
```

### Example 7: Check for delays
```
User: Are there any delays at Salzburg Hauptbahnhof?

Claude: [Uses get_departures]
Current departures from Salzburg Hauptbahnhof:

- RJ 163 to Wien Hauptbahnhof
  Departure: 11:07, Platform 2
  Delay: 5 minutes

- REX 3451 to Zell am See
  Departure: 11:15, Platform 5
  No delay
```

## Checking Arrivals

### Example 8: Expected arrivals
```
User: When will trains arrive at Innsbruck Hauptbahnhof in the next hour?

Claude: [Uses get_arrivals]
Arrivals at Innsbruck Hauptbahnhof:

- IC 593 from Wien Hauptbahnhof
  Arrival: 15:34, Platform 4

- RJ 161 from Zürich HB
  Arrival: 15:48, Platform 3

- S 1 from Telfs-Pfaffenhofen
  Arrival: 15:52, Platform 7
```

## Complex Queries

### Example 9: Multi-leg journey planning
```
User: I need to go from Bregenz to Villach. What's the fastest connection?

Claude: [Uses get_journeys to compare options]
The fastest connection from Bregenz to Villach is:

Journey 1:
- Total duration: 5h 45min
- Transfers: 2

Legs:
1. RJ 162: Bregenz → Innsbruck Hauptbahnhof
   Departs: 08:42, Arrives: 11:09
2. IC 511: Innsbruck Hauptbahnhof → Klagenfurt Hauptbahnhof
   Departs: 11:27, Arrives: 13:58
3. REX 1734: Klagenfurt Hauptbahnhof → Villach Hauptbahnhof
   Departs: 14:15, Arrives: 14:42
```

### Example 10: Finding alternatives
```
User: I missed my train from Wien to Linz. What's the next option?

Claude: [Uses get_departures and get_journeys]
Here are the next trains from Wien Hauptbahnhof to Linz Hauptbahnhof:

Next departure in 12 minutes:
- WESTbahn WB 825
- Departure: 16:42
- Arrival: 18:12
- Duration: 1h 30min
- No transfers

Following departure:
- RJ 661
- Departure: 17:25
- Arrival: 18:43
- Duration: 1h 18min
- No transfers
```

## Tips for Best Results

### 1. Use Clear Station Names
- "Wien Hauptbahnhof" is better than just "Wien"
- "Salzburg Hbf" or "Salzburg Hauptbahnhof" work well

### 2. Specify Times When Needed
- "tomorrow at 2 PM" is clear
- "in the morning" will default to current morning hours

### 3. Ask Follow-up Questions
```
User: Find trains from Graz to Vienna
Claude: [Shows results]
User: What about the one departing at 15:30?
Claude: [Can reference previous search for details]
```

### 4. Combine Queries
```
User: I'm at Linz station now. Show me departures and also plan my trip to Salzburg
Claude: [Uses both get_departures and get_journeys]
```

## Common Use Cases

### Morning Commute
"What time does the next train to work leave from [your station]?"

### Travel Planning
"Plan a day trip from Vienna to Hallstatt with return in the evening"

### Meeting Coordination
"I have a meeting in Graz at 2 PM. What time should I leave from Vienna?"

### Station Monitoring
"Keep me updated on arrivals at Salzburg Hauptbahnhof"

### Delay Checking
"Are there any delays on the Vienna to Innsbruck line?"

## Advanced Features

### Filtering Results
Ask for specific train types:
- "Show only direct connections"
- "I need a train with WiFi" (if supported by API)
- "What's the fastest option?"

### Comparing Options
"Compare morning vs afternoon trains from Linz to Klagenfurt"

### Time-based Planning
"When should I leave to arrive by 10 AM?"

## Notes

- All times are in Central European Time (CET/CEST)
- Real-time data includes current delays and platform changes
- Some information may vary based on HAFAS API availability
- Station names can be in German or English in most cases
