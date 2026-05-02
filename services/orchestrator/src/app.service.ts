import { Injectable } from '@nestjs/common';

@Injectable()
export class AppService {
  health() {
    return {
      status: 'healthy',
      firestoreConnected: false,
      inferenceServiceHealthy: false,
      activeConnections: 0,
    };
  }
}
