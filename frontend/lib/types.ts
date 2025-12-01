// Type definitions for ELCS Frontend

export interface Employee {
  employee_id: number;
  full_name: string;
  phone: string;
  email: string;
  login_name: string;
}

export interface Exhibition {
  ExhibitionId: number;
  Name: string;
  Location: string;
  StartDate: string;
  EndDate: string;
  Description?: string;
  IsActive: boolean;
  CreatedAt?: string;
  UpdatedAt?: string;
}

export interface Lead {
  LeadId: number;
  ExhibitionId: number;
  SourceCode: string;
  AssignedEmployeeId?: number;
  CompanyName?: string;
  PrimaryVisitorName?: string;
  PrimaryVisitorDesignation?: string;
  PrimaryVisitorPhone?: string;
  PrimaryVisitorEmail?: string;
  DiscussionSummary?: string;
  NextStep?: string;
  StatusCode: string;
  WhatsAppConfirmed?: boolean;
  ConfirmedAt?: string;
  CreatedAt: string;
  UpdatedAt: string;
  Segment?: string;
  Priority?: string;

  // Joined fields
  ExhibitionName?: string;
  AssignedEmployeeName?: string;
  SourceName?: string;
  StatusName?: string;
}

export interface LeadPerson {
  LeadPersonId: number;
  LeadId: number;
  Name: string;
  Designation?: string;
  Phone?: string;
  Email?: string;
  IsPrimary: boolean;
}

export interface LeadAddress {
  LeadAddressId: number;
  LeadId: number;
  AddressType?: string;
  AddressText: string;
  City?: string;
  State?: string;
  Country?: string;
  PinCode?: string;
}

export interface LeadAttachment {
  AttachmentId: number;
  LeadId: number;
  AttachmentType: string;
  FileUrl: string;
  FileSizeBytes?: number;
  MimeType?: string;
  CreatedAt: string;
}

export interface LeadMessage {
  MessageId: number;
  LeadId: number;
  SenderType: 'employee' | 'visitor' | 'system';
  SenderEmployeeId?: number;
  MessageText: string;
  WhatsAppMessageId?: string;
  CreatedAt: string;
  SenderEmployeeName?: string;
}

export interface LeadBrand {
  LeadBrandId: number;
  LeadId: number;
  BrandName: string;
  Relationship?: string;
}

export interface LeadPhone {
  LeadPhoneId: number;
  LeadId: number;
  PhoneNumber: string;
  PhoneType?: string;
  IsPrimary?: boolean;
}

export interface LeadEmail {
  LeadEmailId: number;
  LeadId: number;
  EmailAddress: string;
  IsPrimary?: boolean;
}

export interface LeadDetails extends Lead {
  persons: LeadPerson[];
  addresses: LeadAddress[];
  websites: { LeadWebsiteId: number; WebsiteUrl: string }[];
  services: { LeadServiceId: number; ServiceText: string }[];
  topics: { LeadTopicId: number; TopicText: string }[];
  messages: LeadMessage[];
  attachments: LeadAttachment[];
  brands?: LeadBrand[];
  phones?: LeadPhone[];
  emails?: LeadEmail[];
}

export interface CardExtractionResult {
  success: boolean;
  lead_id?: number;
  extraction?: {
    company_name?: string;
    persons: Array<{
      name: string;
      designation?: string;
      phones: string[];
      email?: string;
    }>;
    phones: string[];
    emails: string[];
    websites: string[];
    addresses: Array<{
      address_type?: string;
      address: string;
      city?: string;
      state?: string;
    }>;
    services: string[];
    confidence: number;
  };
  error?: string;
}

export interface VoiceExtractionResult {
  success: boolean;
  lead_id?: number;
  transcript?: string;
  summary?: string;
  topics?: string[];
  next_step?: string;
  segment?: string;
  priority?: string;
  interest_level?: string;
  confidence?: number;
  requires_confirmation?: boolean;
  error?: string;
}

export interface AnalyticsSummary {
  total_leads: number;
  confirmed_leads: number;
  pending_leads: number;
  employee_scan_count: number;
  qr_whatsapp_count: number;
  confirmation_rate: number;
  conversion_rate?: number;
  total_exhibitions?: number;
  active_exhibitions?: number;
  pending_followups?: number;
  completed_followups?: number;
  leads_today?: number;
  leads_this_week?: number;
  leads_this_month?: number;
  needs_correction?: number;
  new_leads?: number;
  leads_by_source?: Array<{ source: string; count: number }>;
  daily_leads?: Array<{ date: string; count: number }>;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  employee_id: number;
  full_name: string;
}

export interface ApiError {
  detail: string;
}
