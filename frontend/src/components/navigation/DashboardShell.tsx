import { Bell, CheckCheck, LogOut, Menu, X, type LucideIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { notificationApi, type NotificationTargetDetail } from "../../services/notificationApi";
import type { Notification } from "../../types/notification";
import { cn } from "../../utils/cn";
import { Button } from "../common/Button";
import { InlineAlert, LoadingState } from "../feedback/FeedbackStates";

export interface NavigationItem {
  label: string;
  to: string;
  icon: LucideIcon;
}

export function DashboardShell({ roleLabel, items }: { roleLabel: string; items: NavigationItem[] }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [notificationsError, setNotificationsError] = useState("");
  const [targetDetail, setTargetDetail] = useState<NotificationTargetDetail | null>(null);
  const [fallbackNotification, setFallbackNotification] = useState<Notification | null>(null);
  const [targetLoading, setTargetLoading] = useState(false);
  const [markingAll, setMarkingAll] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const drawerRef = useRef<HTMLElement>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  useEffect(() => {
    setMobileOpen(false);
    setNotificationsOpen(false);
    setTargetDetail(null);
    setFallbackNotification(null);
  }, [location.pathname, location.hash]);

  useEffect(() => {
    const hash = location.hash.slice(1);
    if (!hash) return;
    const frame = window.requestAnimationFrame(() => {
      document.getElementById(decodeURIComponent(hash))?.scrollIntoView({ block: "start" });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [location.pathname, location.hash]);

  useEffect(() => {
    if (!user) {
      setNotifications([]);
      return;
    }
    let active = true;
    const loadNotifications = (initial = false) => {
      if (initial) setNotificationsLoading(true);
      setNotificationsError("");
      void notificationApi.list()
        .then((items) => { if (active) setNotifications(items); })
        .catch(() => { if (active) setNotificationsError("Notifications are temporarily unavailable."); })
        .finally(() => { if (active && initial) setNotificationsLoading(false); });
    };
    loadNotifications(true);
    const interval = window.setInterval(() => loadNotifications(false), 10000);
    return () => { active = false; window.clearInterval(interval); };
  }, [user]);

  useEffect(() => {
    if (!mobileOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    window.setTimeout(() => drawerRef.current?.focus(), 0);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [mobileOpen]);

  const navigation = (
    <nav aria-label={`${roleLabel} navigation`} className="grid gap-1.5">
      {items.map(({ label, to, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          end={!to.includes("#")}
          onClick={() => setMobileOpen(false)}
          className={({ isActive }) => {
            const hash = to.includes("#") ? to.slice(to.indexOf("#")) : "";
            const selected = isActive && (!hash || location.hash === hash);
            return cn(
              "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-bold transition focus:outline-none focus:ring-2 focus:ring-teal-200",
              selected ? "bg-white/15 text-white" : "text-teal-50/80 hover:bg-white/10 hover:text-white",
            );
          }}
        >
          <Icon size={17} aria-hidden />
          {label}
        </NavLink>
      ))}
    </nav>
  );

  const initials = (user?.email?.trim()[0] ?? user?.phone.slice(-2) ?? "S").toUpperCase();

  const unreadCount = notifications.filter((notification) => !notification.is_read).length;

  const markNotificationRead = (id: number) => {
    void notificationApi.markRead(id)
      .then((updated) => setNotifications((current) => current.map((item) => item.id === updated.id ? updated : item)))
      .catch(() => setNotificationsError("The notification could not be marked as read."));
  };

  const openNotification = async (notificationId: number) => {
    setTargetLoading(true);
    setNotificationsOpen(false);
    setTargetDetail(null);
    setFallbackNotification(null);
    const selected = notifications.find((item) => item.id === notificationId) ?? null;
    try {
      markNotificationRead(notificationId);
      const detail = await notificationApi.targetDetails(notificationId);
      setTargetDetail(detail);
    } catch (caught) {
      // Never leave the user with nothing: show the notification content
      // itself when linked details cannot be loaded.
      if (selected) {
        setFallbackNotification(selected);
        setNotificationsError("");
      } else {
        setNotificationsError(caught instanceof Error ? caught.message : "The linked help-seeking details could not be loaded.");
      }
    } finally { setTargetLoading(false); }
  };

  const markAllNotificationsRead = () => {
    setMarkingAll(true);
    void notificationApi.markAllRead()
      .then(() => setNotifications((current) => current.map((item) => ({ ...item, is_read: true, read_at: item.read_at ?? new Date().toISOString() }))))
      .catch(() => setNotificationsError("Notifications could not be updated."))
      .finally(() => setMarkingAll(false));
  };

  const signOut = async () => {
    setSigningOut(true);
    try {
      await logout();
      navigate("/", { replace: true });
    } finally {
      setSigningOut(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f7f8] text-slate-900">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[248px] flex-col bg-sahaya-900 px-4 py-5 text-white lg:flex">
        <Brand />
        <div className="mt-7 flex-1">{navigation}</div>
        <p className="border-t border-white/10 px-2 pt-4 text-[10px] font-semibold leading-5 text-teal-100/65">
          Authorised access · records shown only when available
        </p>
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button aria-label="Close navigation" className="absolute inset-0 bg-slate-950/50" onClick={() => setMobileOpen(false)} />
          <aside id="mobile-sahaya-navigation" ref={drawerRef} tabIndex={-1} className="relative flex h-full w-[280px] flex-col bg-sahaya-900 px-4 py-5 text-white shadow-2xl focus:outline-none">
            <button aria-label="Close navigation" className="absolute right-3 top-3 rounded-lg p-2 text-white" onClick={() => setMobileOpen(false)}>
              <X size={19} />
            </button>
            <Brand />
            <div className="mt-7 flex-1">{navigation}</div>
          </aside>
        </div>
      ) : null}

      <div className="lg:pl-[248px]">
        <header className="sticky top-0 z-20 flex h-[68px] items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-7">
          <div className="flex items-center gap-3">
            <button
              aria-label="Open navigation"
              aria-expanded={mobileOpen}
              aria-controls="mobile-sahaya-navigation"
              className="rounded-xl border border-slate-200 p-2 text-sahaya-900 focus:outline-none focus:ring-2 focus:ring-sahaya-500 lg:hidden"
              onClick={() => setMobileOpen(true)}
            >
              <Menu size={19} />
            </button>
            <div>
              <p className="text-[10px] font-extrabold uppercase tracking-[0.15em] text-sahaya-700">SAHAYA</p>
              <p className="text-sm font-extrabold text-slate-800">{roleLabel}</p>
            </div>
          </div>
          <div className="relative flex items-center gap-2 sm:gap-3">
            <button
              type="button"
              aria-label="Notifications"
              aria-expanded={notificationsOpen}
              aria-controls="notification-panel"
              className="rounded-xl border border-slate-200 p-2 text-slate-600 focus:outline-none focus:ring-2 focus:ring-sahaya-500"
              onClick={() => setNotificationsOpen((open) => !open)}
            >
              <Bell size={17} />
              {unreadCount > 0 ? <span className="absolute -right-1 -top-1 grid h-4 min-w-4 place-items-center rounded-full bg-red-500 px-1 text-[9px] font-bold text-white">{unreadCount > 9 ? "9+" : unreadCount}</span> : null}
            </button>
            {notificationsOpen ? (
              <section id="notification-panel" className="absolute right-0 top-12 z-30 w-[min(340px,calc(100vw-2rem))] rounded-2xl border border-slate-200 bg-white p-3 shadow-float">
                <div className="mb-2 flex items-center justify-between gap-2 px-1">
                  <div><h2 className="text-sm font-extrabold text-slate-900">Notifications</h2><p className="text-[10px] text-slate-500">{unreadCount} unread</p></div>
                  <div className="flex items-center gap-1">{unreadCount > 0 ? <button type="button" disabled={markingAll} onClick={markAllNotificationsRead} className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-extrabold text-sahaya-700 hover:bg-sahaya-50 disabled:opacity-50"><CheckCheck size={13} /> Mark all read</button> : null}<button aria-label="Close notifications" className="rounded-lg p-1 text-slate-500" onClick={() => setNotificationsOpen(false)}><X size={15} /></button></div>
                </div>
                {notificationsLoading ? <LoadingState label="Loading notifications…" /> : null}
                {!notificationsLoading && notificationsError ? <InlineAlert>{notificationsError}</InlineAlert> : null}
                {!notificationsLoading && !notificationsError && notifications.length === 0 ? <p className="px-2 py-5 text-center text-xs text-slate-500">No notifications yet.</p> : null}
                {!notificationsLoading && !notificationsError && notifications.length > 0 ? <div className="max-h-80 overflow-y-auto">{notifications.map((notification) => <button key={notification.id} type="button" onClick={() => void openNotification(notification.id)} className={`block w-full rounded-xl border-l-2 px-3 py-3 text-left transition hover:bg-slate-50 ${notification.is_read ? "border-l-transparent" : "border-l-red-400 bg-red-50/50"}`}><div className="flex items-start justify-between gap-2"><span className="text-xs font-extrabold text-slate-800">{notification.title}</span>{!notification.is_read ? <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" aria-label="Unread" /> : null}</div><p className="mt-1 text-[11px] leading-5 text-slate-600">{notification.message}</p><time className="mt-1 block text-[10px] text-slate-400" dateTime={notification.created_at}>{new Date(notification.created_at).toLocaleString()}</time></button>)}</div> : null}
              </section>
            ) : null}
            <div className="hidden text-right sm:block">
              <p className="max-w-44 truncate text-xs font-extrabold text-slate-800">{user?.email ?? user?.phone}</p>
              <p className="text-[10px] text-slate-500">{roleLabel}</p>
            </div>
            <div aria-hidden="true" className="grid h-9 w-9 place-items-center rounded-full bg-sahaya-50 text-sm font-extrabold text-sahaya-900">{initials.slice(0, 2)}</div>
            <Button variant="ghost" className="px-2 sm:px-3" loading={signingOut} onClick={() => void signOut()} icon={<LogOut size={15} />}>
              <span className="hidden sm:inline">Sign out</span>
            </Button>
          </div>
        </header>
        {targetLoading ? <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/30 p-4"><div className="rounded-2xl bg-white px-6 py-5 text-sm font-bold shadow-2xl">Loading linked user details…</div></div> : null}
        {fallbackNotification ? <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/45 p-4" onClick={() => setFallbackNotification(null)}><section className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl" onClick={(event) => event.stopPropagation()}><p className="text-[10px] font-extrabold uppercase tracking-[.16em] text-sahaya-700">Notification</p><h2 className="mt-1 text-xl font-extrabold text-slate-900">{fallbackNotification.title}</h2><p className="mt-2 text-sm leading-6 text-slate-600">{fallbackNotification.message}</p><p className="mt-3 text-[11px] text-slate-500">{new Date(fallbackNotification.created_at).toLocaleString()}</p><div className="mt-5 flex justify-end"><button className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-bold" onClick={() => setFallbackNotification(null)}>Close</button></div></section></div> : null}
        {targetDetail ? <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/45 p-4" onClick={() => setTargetDetail(null)}><section className="max-h-[88vh] w-full max-w-3xl overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl" onClick={(event) => event.stopPropagation()}><div className="flex items-start justify-between gap-4"><div><p className="text-[10px] font-extrabold uppercase tracking-[.16em] text-sahaya-700">Help-seeking user</p><h2 className="mt-1 text-xl font-extrabold text-slate-900">{targetDetail.user.full_name}</h2><p className="mt-1 text-xs text-slate-500">{targetDetail.user.display_name} · {targetDetail.user.role}</p></div><button className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-bold" onClick={() => setTargetDetail(null)}>Close</button></div><div className="mt-5 grid gap-3 sm:grid-cols-2"><Info label="Phone" value={targetDetail.user.phone} /><Info label="Email" value={targetDetail.user.email ?? "Not provided"} /><Info label="Date of birth" value={targetDetail.user.date_of_birth ?? "Not provided"} /><Info label="Location" value={[targetDetail.user.district_name, targetDetail.user.state_name].filter(Boolean).join(" · ") || "Not assigned"} /></div>{targetDetail.case ? <div className="mt-5 rounded-2xl border border-slate-200 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><div><p className="text-xs font-extrabold text-slate-900">Case {targetDetail.case.case_number}</p><p className="mt-1 text-[11px] text-slate-500">{targetDetail.case.category} · {targetDetail.case.status} · {targetDetail.case.stage}</p></div>{targetDetail.case.protection_request_open ? <span className="rounded-full bg-red-100 px-2 py-1 text-[10px] font-extrabold text-red-800">Protection request open</span> : null}</div>{targetDetail.case.summary ? <p className="mt-3 text-sm leading-6 text-slate-600">{targetDetail.case.summary}</p> : null}<h3 className="mt-4 text-xs font-extrabold text-slate-800">Documents</h3><div className="mt-2 grid gap-2">{targetDetail.case.documents.length ? targetDetail.case.documents.map((doc) => <div key={doc.id} className="rounded-xl bg-slate-50 p-3 text-xs"><b>{doc.filename}</b><span className="ml-2 text-slate-500">{doc.mime_type} · {doc.status}</span></div>) : <p className="text-xs text-slate-500">No documents uploaded.</p>}</div></div> : <p className="mt-5 text-sm text-slate-500">This notification has no case details.</p>}</section></div> : null}
        <main className="mx-auto max-w-[1320px] p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-3 px-2">
      <span className="grid h-10 w-10 place-items-center rounded-xl bg-teal-100 font-black text-sahaya-900">S</span>
      <div>
        <p className="text-lg font-black tracking-tight">SAHAYA</p>
        <p className="text-[9px] font-bold uppercase tracking-[0.14em] text-teal-100/70">Well-being support</p>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) { return <div className="rounded-xl bg-slate-50 p-3"><p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</p><p className="mt-1 text-sm font-bold text-slate-800">{value}</p></div>; }
