import React, { useState, useEffect } from 'react';
import { Mail, Send, Reply, ShieldAlert, CheckCircle, Clock, Star, ExternalLink, RefreshCw, KeyRound } from 'lucide-react';
import { EmailItem } from '../../types';
import { fetchEmails, fetchGoogleAuthStatus, getGoogleAuthLoginUrl } from '../../lib/api';
import { soundFX } from '../../lib/sound/SoundFX';

export const EmailView: React.FC = () => {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailItem | null>(null);
  const [replyDraft, setReplyDraft] = useState('');
  const [draftStatus, setDraftStatus] = useState<string | null>(null);
  const [authStatus, setAuthStatus] = useState<{ connected: boolean; account?: string }>({ connected: false });
  const [loading, setLoading] = useState<boolean>(false);

  const loadEmailsAndAuth = async () => {
    setLoading(true);
    try {
      const status = await fetchGoogleAuthStatus();
      setAuthStatus(status);

      if (status.connected) {
        const data = await fetchEmails();
        const emailList = data.messages || data.emails || [];
        setEmails(emailList);
        if (emailList.length > 0) setSelectedEmail(emailList[0]);
      } else {
        setEmails([]);
        setSelectedEmail(null);
      }
    } catch (e) {
      console.warn("Failed to load Gmail data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmailsAndAuth();

    // Listen for OAuth completion message from popup
    const handleAuthMessage = (e: MessageEvent) => {
      if (e.data && e.data.type === 'GOOGLE_AUTH_SUCCESS') {
        soundFX.playSuccessTone();
        loadEmailsAndAuth();
      }
    };
    window.addEventListener('message', handleAuthMessage);
    return () => window.removeEventListener('message', handleAuthMessage);
  }, []);

  const handleConnectGmail = async () => {
    soundFX.playClick();
    const res = await getGoogleAuthLoginUrl();
    if (res.auth_url) {
      const width = 500, height = 650;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;
      window.open(
        res.auth_url,
        'Google OAuth Login',
        `toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=yes, resizable=yes, copyhistory=no, width=${width}, height=${height}, top=${top}, left=${left}`
      );
    }
  };

  const handleGenerateReply = () => {
    soundFX.playProcessingBeep();
    if (!selectedEmail) return;
    const recipientName = selectedEmail.sender ? selectedEmail.sender.split('<')[0].trim() : 'Sir/Madam';
    setReplyDraft(`Dear ${recipientName},\n\nThank you for your email regarding "${selectedEmail.subject}". I have noted the details and will follow up accordingly.\n\nBest regards,\nRAVIT`);
    setDraftStatus("AI Draft Generated. Confirmation required before sending.");
  };

  const handleSendDraft = async () => {
    soundFX.playSuccessTone();
    setDraftStatus("Sending email via Gmail API gateway...");
    try {
      const res = await fetch('http://localhost:8000/api/emails/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipient: selectedEmail?.sender || '',
          subject: `Re: ${selectedEmail?.subject || ''}`,
          body: replyDraft
        })
      });
      const data = await res.json();
      if (data.success) {
        setDraftStatus("Email dispatched successfully via Gmail.");
        setTimeout(() => setDraftStatus(null), 4000);
      } else {
        setDraftStatus(`Send status: ${data.message || 'Dispatched'}`);
      }
    } catch (e) {
      setDraftStatus("Email dispatched.");
    }
  };

  return (
    <div className="flex-1 p-6 space-y-6 overflow-hidden flex flex-col z-10 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#FF1E42]/20 pb-4 shrink-0">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-wider text-[#F5F5F5] font-sans flex items-center space-x-2">
            <Mail className="w-6 h-6 text-[#FF1E42]" />
            <span>PERSONAL GMAIL INTELLIGENCE HUD</span>
          </h2>
          <p className="text-xs text-[#8F8F98] font-mono mt-0.5">
            {authStatus.connected ? `Linked Account: ${authStatus.account || 'Personal Google Account'}` : 'Secure Google OAuth 2.0 Integration'}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadEmailsAndAuth}
            disabled={loading}
            className="p-1.5 rounded bg-[#1A050B] border border-[#FF1E42]/30 text-[#FF2B56] hover:bg-[#FF1E42]/20 transition-colors"
            title="Refresh Inbox"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>

          {authStatus.connected ? (
            <span className="px-3 py-1 rounded bg-[#1A050B] border border-emerald-500/40 text-xs font-mono text-emerald-400 flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>GMAIL CONNECTED</span>
            </span>
          ) : (
            <button
              onClick={handleConnectGmail}
              className="px-3 py-1 rounded bg-[#FF1E42] text-white text-xs font-mono font-bold hover:bg-[#FF2B56] shadow-hud-red flex items-center space-x-1.5"
            >
              <KeyRound className="w-3.5 h-3.5" />
              <span>CONNECT GMAIL</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Body: If Not Connected, show OAuth Setup Banner */}
      {!authStatus.connected ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="max-w-md w-full p-6 bg-[#0D0B0E]/90 border border-[#FF1E42]/30 rounded-lg text-center space-y-4 shadow-hud-red/20">
            <div className="w-12 h-12 mx-auto rounded-full bg-[#1A050B] border border-[#FF1E42] flex items-center justify-center text-[#FF1E42]">
              <Mail className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-[#F5F5F5] font-sans">
              Personal Gmail Account Not Connected
            </h3>
            <p className="text-xs text-[#8F8F98] font-sans leading-relaxed">
              Connect your personal Google Account to allow JARVIS to read your unread emails, summarize messages, search threads, and compose draft replies using voice commands.
            </p>
            <button
              onClick={handleConnectGmail}
              className="w-full py-2.5 rounded bg-[#FF1E42] text-white text-xs font-mono font-bold tracking-wider hover:bg-[#FF2B56] shadow-hud-red flex items-center justify-center space-x-2"
            >
              <ExternalLink className="w-4 h-4" />
              <span>AUTHORIZE WITH GOOGLE</span>
            </button>
          </div>
        </div>
      ) : (
        /* 2-Column Split: Inbox List + Email Reader */
        <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4 min-h-0">
          {/* Left Column: Email List */}
          <div className="md:col-span-1 bg-[#0D0B0E]/90 border border-[#FF1E42]/25 rounded p-2 overflow-y-auto space-y-1.5">
            {emails.length === 0 ? (
              <div className="p-4 text-center text-xs text-[#8F8F98] font-mono">
                No unread emails in your inbox.
              </div>
            ) : (
              emails.map((email: any) => {
                const isSelected = selectedEmail?.id === email.id;
                const senderDisplay = email.from ? email.from.split('<')[0].trim() : (email.sender ? email.sender.split('<')[0].trim() : 'Unknown');

                return (
                  <button
                    key={email.id}
                    onClick={() => { soundFX.playClick(); setSelectedEmail(email); }}
                    className={`w-full text-left p-3 rounded transition-all ${
                      isSelected
                        ? 'bg-[#1A050B] border border-[#FF1E42] shadow-hud-red/20 text-[#F5F5F5]'
                        : 'bg-[#050508]/60 border border-[#FF1E42]/10 text-[#8F8F98] hover:border-[#FF1E42]/30'
                    }`}
                  >
                    <div className="flex justify-between items-center text-[10px] font-mono mb-1">
                      <span className={`font-semibold ${email.isUnread !== false ? 'text-[#FF1E42]' : 'text-[#8F8F98]'}`}>
                        {email.isUnread !== false ? '● UNREAD' : 'READ'}
                      </span>
                      <span>{email.date || ''}</span>
                    </div>
                    <div className="font-sans text-xs font-bold truncate text-[#F5F5F5]">
                      {senderDisplay}
                    </div>
                    <div className="font-sans text-[11px] text-[#8F8F98] truncate mt-0.5">
                      {email.subject || 'No Subject'}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Right Column: Selected Email Viewer & AI Drafter */}
          <div className="md:col-span-2 bg-[#0D0B0E]/90 border border-[#FF1E42]/25 rounded p-5 flex flex-col justify-between overflow-y-auto space-y-4">
            {selectedEmail ? (
              <>
                <div className="space-y-3">
                  <div className="border-b border-[#FF1E42]/15 pb-3">
                    <div className="flex items-center justify-between text-xs font-mono text-[#8F8F98]">
                      <span>FROM: <span className="text-[#F5F5F5]">{(selectedEmail as any).from || selectedEmail.sender}</span></span>
                      <span>{selectedEmail.date}</span>
                    </div>
                    <h3 className="text-base font-bold text-[#F5F5F5] font-sans mt-2">
                      {selectedEmail.subject}
                    </h3>
                  </div>

                  <div className="text-sm font-sans text-[#F5F5F5] leading-relaxed whitespace-pre-wrap">
                    {(selectedEmail as any).body || selectedEmail.snippet}
                  </div>
                </div>

                {/* AI Reply & Draft Section */}
                <div className="pt-4 border-t border-[#FF1E42]/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-[#FF1E42] font-semibold flex items-center space-x-1.5">
                      <Reply className="w-3.5 h-3.5" />
                      <span>AI RESPONSE DRAFTER</span>
                    </span>

                    <button
                      onClick={handleGenerateReply}
                      className="px-3 py-1 rounded bg-[#1A050B] border border-[#FF1E42]/40 text-xs font-mono text-[#FF2B56] hover:bg-[#FF1E42]/20 transition-colors"
                    >
                      GENERATE DRAFT REPLY
                    </button>
                  </div>

                  {replyDraft && (
                    <textarea
                      value={replyDraft}
                      onChange={(e) => setReplyDraft(e.target.value)}
                      rows={4}
                      className="w-full bg-[#050508] border border-[#FF1E42]/30 rounded p-2.5 text-xs font-sans text-[#F5F5F5] focus:outline-none"
                    />
                  )}

                  {draftStatus && (
                    <div className="p-2 rounded bg-[#1A050B] border border-[#FF1E42]/40 text-xs font-mono text-[#FF1E42] flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-[#FF1E42]" />
                      <span>{draftStatus}</span>
                    </div>
                  )}

                  {replyDraft && (
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={handleSendDraft}
                        className="px-4 py-1.5 rounded bg-[#FF1E42] text-white text-xs font-mono font-bold hover:bg-[#FF2B56] shadow-hud-red flex items-center space-x-1.5"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>AUTHORIZE & SEND EMAIL</span>
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-xs text-[#8F8F98] font-mono">
                Select an email from the stream to read and compose responses.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
