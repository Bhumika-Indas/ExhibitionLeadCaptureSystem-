// API Client for ELCS Backend

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  Lead,
  LeadDetails,
  Exhibition,
  AnalyticsSummary,
  CardExtractionResult,
  VoiceExtractionResult,
} from './types';

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.clearToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login';
          }
        }
        return Promise.reject(error);
      }
    );

    // Load token from localStorage on init
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('employee');
    }
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const { data } = await this.client.post<LoginResponse>('/api/auth/login', credentials);
    this.setToken(data.access_token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('employee', JSON.stringify({
        employee_id: data.employee_id,
        full_name: data.full_name,
      }));
    }
    return data;
  }

  logout() {
    this.clearToken();
  }

  // Exhibitions
  async getExhibitions(): Promise<Exhibition[]> {
    const { data } = await this.client.get('/api/exhibitions/');
    return data.exhibitions || [];
  }

  async createExhibition(exhibition: {
    name: string;
    location?: string;
    start_date: string;
    end_date: string;
    description?: string;
  }): Promise<{ success: boolean; exhibition_id: number }> {
    const { data } = await this.client.post('/api/exhibitions/', exhibition);
    return data;
  }

  // Leads
  async getLeads(params?: {
    exhibition_id?: number;
    source_code?: string;
    status_code?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ leads: Lead[]; count: number }> {
    const { data } = await this.client.get('/api/leads', { params });
    return data;
  }

  async getLead(leadId: number): Promise<LeadDetails> {
    const { data } = await this.client.get(`/api/leads/${leadId}`);
    // Merge lead data with related entities for LeadDetails
    return {
      ...data.lead,
      persons: data.persons || [],
      addresses: data.addresses || [],
      websites: data.websites || [],
      services: data.services || [],
      topics: data.topics || [],
      messages: data.messages || [],
      attachments: data.attachments || [],
      brands: data.brands || [],
      phones: data.phones || [],
      emails: data.emails || [],
    };
  }

  async createLead(leadData: Partial<Lead>): Promise<{ lead_id: number }> {
    const { data } = await this.client.post('/api/leads', leadData);
    return data;
  }

  async updateLead(leadId: number, updates: Partial<Lead>): Promise<void> {
    await this.client.put(`/api/leads/${leadId}`, updates);
  }

  async addMessage(
    leadId: number,
    senderType: string,
    messageText: string,
    senderEmployeeId?: number
  ): Promise<{ message_id: number }> {
    const { data } = await this.client.post(`/api/leads/${leadId}/messages`, {
      sender_type: senderType,
      message_text: messageText,
      sender_employee_id: senderEmployeeId,
    });
    return data;
  }

  async sendGreetingAfterVerification(leadId: number): Promise<{ success: boolean; message: string }> {
    const { data } = await this.client.post(`/api/leads/${leadId}/send-greeting`);
    return data;
  }

  async getLeadJourney(leadId: number): Promise<{
    success: boolean;
    lead_id: number;
    lead_name: string;
    company_name: string;
    current_status: string;
    timeline: Array<{
      id: string;
      type: string;
      title: string;
      description: string;
      timestamp: string;
      icon: string;
      color: string;
      metadata: any;
    }>;
    total_events: number;
  }> {
    const { data } = await this.client.get(`/api/leads/${leadId}/journey`);
    return data;
  }

  // Card Extraction
  async extractCard(
    frontImage: File,
    backImage: File | null,
    exhibitionId: number,
    employeeId: number
  ): Promise<CardExtractionResult> {
    const formData = new FormData();
    formData.append('front_image', frontImage);
    if (backImage) {
      formData.append('back_image', backImage);
    }
    formData.append('exhibition_id', exhibitionId.toString());
    formData.append('employee_id', employeeId.toString());

    const { data } = await this.client.post<CardExtractionResult>(
      '/api/extraction/card',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000, // 60 seconds for card processing
      }
    );
    return data;
  }

  // Voice Extraction
  async extractVoice(
    audioFile: Blob,
    leadId: number,
    employeeId?: number
  ): Promise<VoiceExtractionResult> {
    const formData = new FormData();
    formData.append('audio_file', audioFile, 'voice_note.webm');
    formData.append('lead_id', leadId.toString());
    if (employeeId) {
      formData.append('employee_id', employeeId.toString());
    }

    const { data } = await this.client.post<VoiceExtractionResult>(
      '/api/extraction/voice',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      }
    );
    return data;
  }

  // Confirm Voice Analysis
  async confirmVoiceAnalysis(params: {
    lead_id: number;
    summary: string;
    next_step?: string;
    segment: string;
    priority: string;
    interest_level?: string;
  }): Promise<{ success: boolean; message: string }> {
    const formData = new FormData();
    formData.append('lead_id', params.lead_id.toString());
    formData.append('summary', params.summary);
    if (params.next_step) formData.append('next_step', params.next_step);
    formData.append('segment', params.segment);
    formData.append('priority', params.priority);
    if (params.interest_level) formData.append('interest_level', params.interest_level);

    const { data } = await this.client.post(
      '/api/extraction/voice/confirm',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  }

  // WhatsApp
  async sendConfirmation(leadId: number): Promise<void> {
    await this.client.post(`/api/whatsapp/send-confirmation/${leadId}`);
  }

  // Analytics
  async getAnalyticsSummary(exhibitionId?: number): Promise<AnalyticsSummary> {
    const { data } = await this.client.get('/api/analytics/summary', {
      params: exhibitionId ? { exhibition_id: exhibitionId } : undefined,
    });
    return data;
  }

  async getEmployeePerformance(exhibitionId?: number) {
    const { data } = await this.client.get('/api/analytics/employee-performance', {
      params: exhibitionId ? { exhibition_id: exhibitionId } : undefined,
    });
    return data.data || [];
  }

  // Follow-ups
  async getFollowupStats(): Promise<{
    total: number;
    pending: number;
    completed: number;
    cancelled: number;
    failed: number;
  }> {
    const { data } = await this.client.get('/api/followups/stats');
    return data;
  }

  async getFollowups(params?: {
    status?: string;
    lead_id?: number;
    limit?: number;
  }): Promise<any[]> {
    const { data } = await this.client.get('/api/followups/', { params });
    return data;
  }

  async createFollowup(followupData: {
    lead_id: number;
    action_type: string;
    scheduled_at: string;
    notes?: string;
  }): Promise<any> {
    const { data} = await this.client.post('/api/followups/', followupData);
    return data;
  }

  async updateFollowup(
    followupId: number,
    updates: {
      status?: string;
      notes?: string;
      completed_at?: string;
    }
  ): Promise<any> {
    const { data } = await this.client.put(`/api/followups/${followupId}`, updates);
    return data;
  }

  async processPendingFollowups(): Promise<{ processed_count: number }> {
    const { data } = await this.client.post('/api/followups/process-pending');
    return data;
  }

  async scheduleDripSequence(leadId: number): Promise<void> {
    await this.client.post(`/api/followups/lead/${leadId}/schedule-drip`);
  }

  async cancelDripSequence(leadId: number): Promise<void> {
    await this.client.post(`/api/followups/lead/${leadId}/cancel-drip`);
  }

  // Messages (for chat screen)
  async getLeadMessages(leadId: number): Promise<any[]> {
    const { data } = await this.client.get(`/api/leads/${leadId}/messages`);
    return data.messages || [];
  }

  async getRecentConversations(limit: number = 50): Promise<any[]> {
    // Get recent leads with messages
    const { data } = await this.client.get('/api/leads', {
      params: { limit, offset: 0 }
    });
    return data.leads || [];
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; database: string }> {
    const { data } = await this.client.get('/health');
    return data;
  }

  // Scheduler Status
  async getSchedulerStatus(): Promise<{
    status: string;
    jobs: Array<{
      id: string;
      name: string;
      next_run: string | null;
      trigger: string;
    }>;
  }> {
    const { data } = await this.client.get('/scheduler/status');
    return data;
  }

  // ==================== DRIP SYSTEM V2 ====================

  // Message Master
  async getMessages(activeOnly: boolean = true): Promise<any[]> {
    const { data } = await this.client.get('/api/drip/messages', {
      params: { active_only: activeOnly }
    });
    return data.messages || [];
  }

  async getMessage(messageId: number): Promise<any> {
    const { data } = await this.client.get(`/api/drip/messages/${messageId}`);
    return data.message;
  }

  async createMessage(message: {
    title: string;
    message_type: string;
    body?: string;
    variables?: string[];
  }): Promise<{ message_id: number }> {
    const { data } = await this.client.post('/api/drip/messages', message);
    return data;
  }

  async updateMessage(messageId: number, updates: {
    title?: string;
    message_type?: string;
    body?: string;
    variables?: string[];
    is_active?: boolean;
  }): Promise<void> {
    await this.client.put(`/api/drip/messages/${messageId}`, updates);
  }

  async deleteMessage(messageId: number): Promise<void> {
    await this.client.delete(`/api/drip/messages/${messageId}`);
  }

  // Drip Master
  async getDrips(activeOnly: boolean = true): Promise<any[]> {
    const { data } = await this.client.get('/api/drip/drips', {
      params: { active_only: activeOnly }
    });
    return data.drips || [];
  }

  async getDrip(dripId: number): Promise<any> {
    const { data } = await this.client.get(`/api/drip/drips/${dripId}`);
    return data.drip;
  }

  async createDrip(drip: {
    name: string;
    description?: string;
  }): Promise<{ drip_id: number }> {
    const { data } = await this.client.post('/api/drip/drips', drip);
    return data;
  }

  async updateDrip(dripId: number, updates: {
    name?: string;
    description?: string;
    is_active?: boolean;
  }): Promise<void> {
    await this.client.put(`/api/drip/drips/${dripId}`, updates);
  }

  async deleteDrip(dripId: number): Promise<void> {
    await this.client.delete(`/api/drip/drips/${dripId}`);
  }

  async addMessageToDrip(dripId: number, message: {
    message_id: number;
    day_number: number;
    send_time: string;
    sort_order?: number;
  }): Promise<{ drip_message_id: number }> {
    const { data } = await this.client.post(`/api/drip/drips/${dripId}/messages`, message);
    return data;
  }

  async updateDripMessage(dripMessageId: number, updates: {
    day_number?: number;
    send_time?: string;
    sort_order?: number;
  }): Promise<void> {
    await this.client.put(`/api/drip/drips/messages/${dripMessageId}`, updates);
  }

  async removeDripMessage(dripMessageId: number): Promise<void> {
    await this.client.delete(`/api/drip/drips/messages/${dripMessageId}`);
  }

  // Drip Assignments
  async applyDripToLead(leadId: number, dripId: number): Promise<{ assignment_id: number }> {
    const { data } = await this.client.post('/api/drip/apply', {
      lead_id: leadId,
      drip_id: dripId
    });
    return data;
  }

  async stopDrip(leadId: number, assignmentId?: number): Promise<void> {
    await this.client.post(`/api/drip/lead/${leadId}/stop`, null, {
      params: assignmentId ? { assignment_id: assignmentId } : undefined
    });
  }

  async pauseDrip(leadId: number, assignmentId?: number): Promise<void> {
    await this.client.post(`/api/drip/lead/${leadId}/pause`, null, {
      params: assignmentId ? { assignment_id: assignmentId } : undefined
    });
  }

  async resumeDrip(leadId: number, assignmentId?: number): Promise<void> {
    await this.client.post(`/api/drip/lead/${leadId}/resume`, null, {
      params: assignmentId ? { assignment_id: assignmentId } : undefined
    });
  }

  async getLeadDripStatus(leadId: number): Promise<{
    assignment: any;
    scheduled_messages: any[];
  }> {
    const { data } = await this.client.get(`/api/drip/lead/${leadId}/status`);
    return data;
  }

  async skipScheduledMessage(scheduledId: number): Promise<void> {
    await this.client.post(`/api/drip/messages/${scheduledId}/skip`);
  }

  async getDripAssignments(status?: string, limit: number = 100): Promise<any[]> {
    const { data } = await this.client.get('/api/drip/assignments', {
      params: { status, limit }
    });
    return data.assignments || [];
  }

  async processDripMessages(): Promise<{ processed: number; failed: number }> {
    const { data } = await this.client.post('/api/drip/process');
    return data;
  }
}

// Export singleton instance
export const api = new ApiClient();
