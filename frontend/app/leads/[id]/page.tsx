'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import toast from 'react-hot-toast';
import { api } from '@/lib/api';
import { requireAuth } from '@/lib/auth';
import type { LeadDetails } from '@/lib/types';
import DripSequenceCard from '@/components/DripSequenceCard';

export default function LeadDetailPage() {
  const router = useRouter();
  const params = useParams();
  const leadId = parseInt(params.id as string);

  const [lead, setLead] = useState<LeadDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [sendingGreeting, setSendingGreeting] = useState(false);

  useEffect(() => {
    try {
      requireAuth();
      loadLead();
    } catch {
      router.push('/auth/login');
    }
  }, [leadId]);

  const loadLead = async () => {
    try {
      const data = await api.getLead(leadId);
      setLead(data);
    } catch (error) {
      console.error('Failed to load lead:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendGreeting = async () => {
    if (!lead?.PrimaryVisitorPhone) {
      toast.error('No phone number found for this lead');
      return;
    }

    if (!confirm(`Send WhatsApp greeting to ${lead.PrimaryVisitorName || 'visitor'}?`)) {
      return;
    }

    setSendingGreeting(true);
    try {
      const result = await api.sendGreetingAfterVerification(leadId);
      toast.success(result.message);
      // Reload lead to see updated status
      await loadLead();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || 'Failed to send greeting');
    } finally {
      setSendingGreeting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!lead) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Lead not found</p>
          <button onClick={() => router.push('/leads')} className="mt-4 text-blue-600 underline">
            Back to Leads
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/30 pb-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 text-white sticky top-0 z-10 shadow-lg">
        <div className="max-w-lg mx-auto px-4 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.back()}
                className="text-white hover:bg-white/20 p-2 rounded-lg transition-all duration-200 active:scale-95"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div>
                <h1 className="text-xl font-bold">Lead Details</h1>
                <p className="text-xs text-blue-100 mt-0.5">View and manage lead information</p>
              </div>
            </div>
            <span className={`px-3 py-1.5 rounded-full text-xs font-semibold shadow-sm ${
              lead.StatusCode === 'new' ? 'bg-yellow-400 text-yellow-900' :
              lead.StatusCode === 'contacted' ? 'bg-blue-400 text-blue-900' :
              lead.StatusCode === 'qualified' ? 'bg-purple-400 text-purple-900' :
              lead.StatusCode === 'converted' ? 'bg-green-400 text-green-900' :
              'bg-white/30 text-white'
            }`}>
              {lead.StatusName || lead.StatusCode}
            </span>
          </div>
        </div>
      </div>

      {/* Content - Mobile Optimized */}
      <div className="max-w-lg mx-auto px-4 py-5 space-y-5">

        {/* Quick Actions Card */}
        <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-5 hover:shadow-lg transition-shadow duration-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Quick Actions
          </h3>
          <button
            onClick={handleSendGreeting}
            disabled={sendingGreeting || !lead.PrimaryVisitorPhone}
            className={`w-full flex items-center justify-center gap-2 px-4 py-3.5 rounded-xl font-semibold transition-all duration-200 text-sm shadow-sm ${
              sendingGreeting || !lead.PrimaryVisitorPhone
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-green-500 to-green-600 text-white hover:from-green-600 hover:to-green-700 hover:shadow-md active:scale-95'
            }`}
          >
            {sendingGreeting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Sending...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                </svg>
                {!lead.PrimaryVisitorPhone ? 'No Phone' : 'WhatsApp'}
              </>
            )}
          </button>
        </div>

        {/* Drip Sequence Section */}
        <DripSequenceCard leadId={leadId} />

        {/* Visiting Card Images - TOP PRIORITY */}
        {lead.attachments && lead.attachments.filter((a) => a.AttachmentType.includes('card')).length > 0 && (
          <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-5 hover:shadow-lg transition-shadow duration-200">
            <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
              </div>
              Visiting Card
            </h2>
            <div className={`grid ${lead.attachments.filter((a) => a.AttachmentType.includes('card')).length > 1 ? 'grid-cols-2' : 'grid-cols-1'} gap-4`}>
              {lead.attachments
                .filter((a) => a.AttachmentType.includes('card'))
                .map((attachment) => (
                  <div key={attachment.AttachmentId} className="relative group">
                    <img
                      src={`http://localhost:8000${attachment.FileUrl}`}
                      alt={attachment.AttachmentType}
                      className="w-full rounded-xl border-2 border-gray-200 shadow-md group-hover:shadow-xl transition-all duration-200 group-hover:scale-[1.02]"
                    />
                    <span className="absolute top-3 right-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white text-xs font-semibold px-3 py-1.5 rounded-full capitalize shadow-lg">
                      {attachment.AttachmentType.replace('card_', '')}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Primary Contact Info */}
        <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-5 hover:shadow-lg transition-shadow duration-200">
          <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            Contact Information
          </h2>

          <div className="space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <p className="font-bold text-gray-900 text-lg">{lead.PrimaryVisitorName || 'Not provided'}</p>
                {lead.PrimaryVisitorDesignation && (
                  <p className="text-sm text-gray-600 mt-1 flex items-center gap-1">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    {lead.PrimaryVisitorDesignation}
                  </p>
                )}
                {lead.CompanyName && (
                  <p className="text-sm font-semibold text-blue-600 mt-2 flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    {lead.CompanyName}
                  </p>
                )}
              </div>
              {lead.WhatsAppConfirmed && (
                <span className="bg-gradient-to-r from-green-500 to-green-600 text-white text-xs font-semibold px-3 py-1.5 rounded-full shadow-sm flex items-center gap-1">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  WhatsApp
                </span>
              )}
            </div>

            {lead.PrimaryVisitorPhone && (
              <a
                href={`tel:${lead.PrimaryVisitorPhone}`}
                className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition"
              >
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Phone</p>
                  <p className="font-medium text-blue-600">{lead.PrimaryVisitorPhone}</p>
                </div>
              </a>
            )}

            {lead.PrimaryVisitorEmail && (
              <a
                href={`mailto:${lead.PrimaryVisitorEmail}`}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
              >
                <div className="w-10 h-10 bg-gray-600 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Email</p>
                  <p className="font-medium text-gray-700 break-all">{lead.PrimaryVisitorEmail}</p>
                </div>
              </a>
            )}
          </div>
        </div>

        {/* Segment & Priority - Lead Intelligence */}
        {(lead.Segment || lead.Priority || lead.NextStep) && (
          <div className="bg-white rounded-xl shadow-sm p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Lead Intelligence
            </h2>
            <div className="space-y-3">
              <div className="flex gap-3">
                {lead.Segment && (
                  <div className="flex-1 p-3 bg-indigo-50 rounded-lg">
                    <p className="text-xs text-indigo-500 mb-1">Segment</p>
                    <p className={`font-semibold capitalize ${
                      lead.Segment === 'decision_maker' ? 'text-indigo-700' :
                      lead.Segment === 'influencer' ? 'text-blue-700' :
                      lead.Segment === 'researcher' ? 'text-cyan-700' :
                      'text-gray-700'
                    }`}>
                      {lead.Segment.replace('_', ' ')}
                    </p>
                  </div>
                )}
                {lead.Priority && (
                  <div className={`flex-1 p-3 rounded-lg ${
                    lead.Priority === 'high' ? 'bg-red-50' :
                    lead.Priority === 'medium' ? 'bg-yellow-50' :
                    'bg-green-50'
                  }`}>
                    <p className={`text-xs mb-1 ${
                      lead.Priority === 'high' ? 'text-red-500' :
                      lead.Priority === 'medium' ? 'text-yellow-600' :
                      'text-green-500'
                    }`}>Priority</p>
                    <p className={`font-semibold capitalize ${
                      lead.Priority === 'high' ? 'text-red-700' :
                      lead.Priority === 'medium' ? 'text-yellow-700' :
                      'text-green-700'
                    }`}>
                      {lead.Priority}
                    </p>
                  </div>
                )}
              </div>
              {lead.NextStep && (
                <div className="p-3 bg-emerald-50 rounded-lg">
                  <p className="text-xs text-emerald-500 mb-1">Next Step</p>
                  <p className="font-medium text-emerald-700">{lead.NextStep}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Company Information */}
        <div className="bg-white rounded-xl shadow-sm p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            Company
          </h2>

          <div className="space-y-3">
            <div>
              <p className="font-semibold text-gray-900">{lead.CompanyName || 'Not provided'}</p>
            </div>

            {lead.websites && lead.websites.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 mb-1">Website</p>
                {lead.websites.map((w) => (
                  <a
                    key={w.LeadWebsiteId}
                    href={w.WebsiteUrl.startsWith('http') ? w.WebsiteUrl : `https://${w.WebsiteUrl}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline text-sm block"
                  >
                    {w.WebsiteUrl}
                  </a>
                ))}
              </div>
            )}

            {lead.addresses && lead.addresses.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 mb-1">Address</p>
                {lead.addresses.map((addr) => (
                  <div key={addr.LeadAddressId} className="text-sm text-gray-700">
                    {addr.AddressType && (
                      <span className="text-xs bg-gray-100 px-2 py-0.5 rounded mr-2">{addr.AddressType}</span>
                    )}
                    <p className="mt-1">{addr.AddressText}</p>
                    {addr.City && <p className="text-gray-500">{addr.City}{addr.State && `, ${addr.State}`}</p>}
                  </div>
                ))}
              </div>
            )}

            {lead.services && lead.services.length > 0 && (
              <div>
                <p className="text-xs text-gray-500 mb-2">Products/Services</p>
                <div className="flex flex-wrap gap-2">
                  {lead.services.map((s) => (
                    <span key={s.LeadServiceId} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                      {s.ServiceText}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Associated Brands (for dealer cards) */}
        {lead.brands && lead.brands.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
              Associated Brands
            </h2>
            <div className="space-y-2">
              {lead.brands.map((brand) => (
                <div key={brand.LeadBrandId} className="flex items-center justify-between p-2 bg-purple-50 rounded-lg">
                  <span className="font-medium text-purple-900">{brand.BrandName}</span>
                  {brand.Relationship && (
                    <span className="text-xs bg-purple-200 text-purple-700 px-2 py-1 rounded-full">
                      {brand.Relationship}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All Phone Numbers */}
        {lead.phones && lead.phones.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
              All Phone Numbers ({lead.phones.length})
            </h2>
            <div className="space-y-2">
              {lead.phones.map((phone) => (
                <a
                  key={phone.LeadPhoneId}
                  href={`tel:${phone.PhoneNumber}`}
                  className="flex items-center justify-between p-2 bg-green-50 rounded-lg hover:bg-green-100 transition"
                >
                  <span className="font-medium text-green-700">{phone.PhoneNumber}</span>
                  {phone.PhoneType && (
                    <span className="text-xs bg-green-200 text-green-700 px-2 py-1 rounded-full">
                      {phone.PhoneType}
                    </span>
                  )}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* All Email Addresses */}
        {lead.emails && lead.emails.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              All Email Addresses ({lead.emails.length})
            </h2>
            <div className="space-y-2">
              {lead.emails.map((email) => (
                <a
                  key={email.LeadEmailId}
                  href={`mailto:${email.EmailAddress}`}
                  className="flex items-center p-2 bg-orange-50 rounded-lg hover:bg-orange-100 transition"
                >
                  <span className="font-medium text-orange-700 break-all">{email.EmailAddress}</span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Additional Persons */}
        {lead.persons && lead.persons.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Additional Contacts
            </h2>
            <div className="space-y-3">
              {lead.persons.map((person) => (
                <div key={person.LeadPersonId} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
                  <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center text-gray-600 font-medium">
                    {person.Name?.charAt(0).toUpperCase() || '?'}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{person.Name}</p>
                    {person.Designation && <p className="text-xs text-gray-500">{person.Designation}</p>}
                    {person.Phone && <p className="text-sm text-blue-600">{person.Phone}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Discussion Summary */}
        {lead.DiscussionSummary && (
          <div className="bg-white rounded-xl shadow-sm p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              Discussion Summary
            </h2>
            <p className="text-sm text-gray-600">{lead.DiscussionSummary}</p>
          </div>
        )}

        {/* Conversation History */}
        {lead.messages && lead.messages.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
              </svg>
              Conversation History
            </h2>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {lead.messages.map((message) => (
                <div
                  key={message.MessageId}
                  className={`p-3 rounded-lg text-sm ${
                    message.SenderType === 'system'
                      ? 'bg-gray-100 text-gray-600 text-center'
                      : message.SenderType === 'employee'
                      ? 'bg-blue-100 text-blue-900 ml-8'
                      : 'bg-gray-100 text-gray-900 mr-8'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.MessageText}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(message.CreatedAt).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Journey Timeline Modal */}
        {showJourney && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
            <div className="bg-white w-full max-w-2xl max-h-[90vh] rounded-t-2xl sm:rounded-2xl shadow-2xl flex flex-col">
              {/* Modal Header */}
              <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-4 rounded-t-2xl flex items-center justify-between sticky top-0 z-10">
                <div>
                  <h2 className="text-xl font-bold">Lead Journey</h2>
                  {journeyData && (
                    <p className="text-sm text-white/80 mt-1">
                      {journeyData.lead_name} {journeyData.company_name ? `• ${journeyData.company_name}` : ''}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => setShowJourney(false)}
                  className="text-white hover:bg-white/20 rounded-lg p-2 transition"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Timeline Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {loadingJourney ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
                  </div>
                ) : journeyData && journeyData.timeline && journeyData.timeline.length > 0 ? (
                  <div className="relative">
                    {/* Vertical Timeline Line */}
                    <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200"></div>

                    {/* Timeline Events */}
                    <div className="space-y-6">
                      {journeyData.timeline.map((event: any) => {
                        const colorMap: Record<string, string> = {
                          blue: 'bg-blue-500',
                          green: 'bg-green-500',
                          purple: 'bg-purple-500',
                          orange: 'bg-orange-500',
                          indigo: 'bg-indigo-500',
                          teal: 'bg-teal-500',
                          yellow: 'bg-yellow-500',
                          gray: 'bg-gray-400',
                          red: 'bg-red-500'
                        };
                        const colorClasses = colorMap[event.color] || 'bg-blue-500';

                        return (
                          <div key={event.id} className="relative flex gap-4">
                            {/* Icon Circle */}
                            <div className={`relative z-10 flex-shrink-0 w-12 h-12 ${colorClasses} rounded-full flex items-center justify-center text-white shadow-lg`}>
                              {event.icon === 'user_plus' && (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                                </svg>
                              )}
                              {event.icon === 'whatsapp' && (
                                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                                </svg>
                              )}
                              {event.icon === 'status' && (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              )}
                              {event.icon === 'calendar' && (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                              )}
                              {event.icon === 'auto_message' && (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                </svg>
                              )}
                              {event.icon === 'presentation' && (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                                </svg>
                              )}
                              {event.icon === 'phone' && (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                                </svg>
                              )}
                              {event.icon === 'document' && (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                              )}
                              {event.icon === 'note' && (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                              )}
                              {!['user_plus', 'whatsapp', 'status', 'calendar', 'auto_message', 'presentation', 'phone', 'document', 'note'].includes(event.icon) && (
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              )}
                            </div>

                            {/* Event Content */}
                            <div className="flex-1 pb-6">
                              <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition">
                                <div className="flex items-start justify-between gap-2">
                                  <h3 className="font-semibold text-gray-900">{event.title}</h3>
                                  <span className="text-xs text-gray-500 whitespace-nowrap">
                                    {event.timestamp ? new Date(event.timestamp).toLocaleString('en-US', {
                                      month: 'short',
                                      day: 'numeric',
                                      hour: '2-digit',
                                      minute: '2-digit'
                                    }) : 'N/A'}
                                  </span>
                                </div>
                                <p className="text-sm text-gray-600 mt-2">{event.description}</p>

                                {/* Metadata Tags */}
                                {event.metadata && Object.keys(event.metadata).length > 0 && (
                                  <div className="flex flex-wrap gap-2 mt-3">
                                    {Object.entries(event.metadata).map(([key, value]: [string, any]) => {
                                      if (value && key !== 'scheduled_at') {
                                        return (
                                          <span key={key} className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">
                                            <span className="font-medium">{key.replace(/_/g, ' ')}:</span>
                                            <span className="ml-1">{String(value)}</span>
                                          </span>
                                        );
                                      }
                                      return null;
                                    })}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Summary Footer */}
                    <div className="mt-8 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-700 font-medium">Total Events: {journeyData.total_events}</span>
                        <span className="text-gray-700">Current Status: <span className="font-semibold text-purple-700">{journeyData.current_status}</span></span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <p>No journey events found for this lead</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
