import http from 'k6/http';
import { check, group, sleep } from 'k6';

// Load test configuration
export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Ramp-up: 0 → 20 users
    { duration: '1m30s', target: 20 }, // Stay at 20 users
    { duration: '30s', target: 40 },   // Ramp-up: 20 → 40 users
    { duration: '1m30s', target: 40 }, // Stay at 40 users
    { duration: '30s', target: 0 },    // Ramp-down: 40 → 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% < 500ms, 99% < 1s
    http_req_failed: ['rate<0.1'],                   // <10% failure rate
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Test 1: Page Load
  group('Load Page', () => {
    const response = http.get(`${BASE_URL}/`);
    check(response, {
      'page loads': (r) => r.status === 200,
      'page size > 0': (r) => r.body.length > 0,
      'no 5xx errors': (r) => r.status < 500,
    });
  });

  sleep(1);

  // Test 2: Map API Call Simulation
  group('Map Data Request', () => {
    // Simulate map tile loading
    const tileResponse = http.get(`https://tile.openstreetmap.org/12/2048/1024.png`, {
      tags: { name: 'MapTile' },
    });

    check(tileResponse, {
      'tile loads': (r) => r.status === 200 || r.status === 304,
    });
  });

  sleep(2);

  // Test 3: CSS/JS Resource Loading
  group('Asset Loading', () => {
    const batch = http.batch([
      ['GET', `${BASE_URL}/`],
      ['HEAD', `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css`],
      ['HEAD', `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js`],
    ]);

    check(batch, {
      'assets load': (r) => r.some(res => res.status === 200 || res.status === 304),
    });
  });

  sleep(1);

  // Test 4: Simulate User Interaction Sequence
  group('User Interaction Sequence', () => {
    // Multiple rapid page reloads (simulating filter changes)
    for (let i = 0; i < 3; i++) {
      const response = http.get(`${BASE_URL}/`, {
        tags: { name: 'PageReload' },
      });

      check(response, {
        'page responsive': (r) => r.status === 200,
        'no timeouts': (r) => r.timings.duration < 5000,
      });

      sleep(0.5);
    }
  });

  sleep(2);
}
