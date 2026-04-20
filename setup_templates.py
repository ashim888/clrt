"""Template generator for CLRT project."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w') as f:
        f.write(content)
    print(f"  wrote {path}")

# ─── static/css/app.css (Tailwind via CDN, we'll use inline CDN in base) ──────
write('static/css/app.css', '/* Custom overrides */')
write('static/js/app.js', '// CLRT JS')

# ══════════════════════════════════════════════════════════════════
# BASE TEMPLATE
# ══════════════════════════════════════════════════════════════════
write('templates/base.html', '''<!DOCTYPE html>
<html lang="en" class="h-full bg-gray-50">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{% block title %}CLRT{% endblock %} | Client Lifecycle & Revenue Tracker</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: { 50:'#eff6ff', 500:'#3b82f6', 600:'#2563eb', 700:'#1d4ed8' }
          }
        }
      }
    }
  </script>
  <style>
    .input { @apply block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none; }
    .btn { @apply inline-flex items-center rounded-md px-4 py-2 text-sm font-medium transition-colors; }
    .btn-primary { @apply btn bg-blue-600 text-white hover:bg-blue-700; }
    .btn-secondary { @apply btn bg-white text-gray-700 border border-gray-300 hover:bg-gray-50; }
    .btn-danger { @apply btn bg-red-600 text-white hover:bg-red-700; }
    .badge { @apply inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium; }
    .card { @apply bg-white rounded-xl border border-gray-200 shadow-sm; }
  </style>
  {% block extra_head %}{% endblock %}
</head>
<body class="h-full">

{% if user.is_authenticated %}
<!-- Sidebar layout -->
<div class="flex h-full">
  <!-- Sidebar -->
  <aside class="w-60 flex-shrink-0 bg-gray-900 flex flex-col">
    <div class="px-5 py-5 border-b border-gray-700">
      <span class="text-white font-bold text-lg tracking-tight">&#x1F4CB; CLRT</span>
      <p class="text-gray-400 text-xs mt-0.5">CRM & Revenue Tracker</p>
    </div>
    <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
      <a href="/" class="nav-link group flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-800 hover:text-white {% block nav_dashboard %}{% endblock %}">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
        Dashboard
      </a>
      <a href="/leads/" class="nav-link group flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-800 hover:text-white {% block nav_leads %}{% endblock %}">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
        Leads
      </a>
      <a href="/clients/" class="nav-link group flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-800 hover:text-white {% block nav_clients %}{% endblock %}">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
        Clients
      </a>
      <a href="/billing/" class="nav-link group flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-800 hover:text-white {% block nav_billing %}{% endblock %}">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21l-7-2-7 2V5a2 2 0 012-2h10a2 2 0 012 2v16z"/></svg>
        Billing
      </a>
      {% if user.is_admin %}
      <a href="/accounts/users/" class="nav-link group flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-800 hover:text-white {% block nav_users %}{% endblock %}">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
        Users
      </a>
      {% endif %}
    </nav>
    <div class="px-3 py-4 border-t border-gray-700">
      <div class="flex items-center gap-3 px-3 py-2">
        <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">
          {{ user.username|slice:":2"|upper }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm text-white truncate">{{ user.get_full_name|default:user.username }}</p>
          <p class="text-xs text-gray-400">{{ user.get_role_display }}</p>
        </div>
        <a href="/accounts/logout/" class="text-gray-400 hover:text-white" title="Logout">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
        </a>
      </div>
    </div>
  </aside>

  <!-- Main content -->
  <main class="flex-1 overflow-y-auto">
    <div class="max-w-7xl mx-auto px-6 py-6">
      {% if messages %}
      <div class="mb-4 space-y-2">
        {% for message in messages %}
        <div class="rounded-lg px-4 py-3 text-sm flex items-center gap-2
          {% if message.tags == 'error' %}bg-red-50 text-red-800 border border-red-200
          {% elif message.tags == 'success' %}bg-green-50 text-green-800 border border-green-200
          {% else %}bg-blue-50 text-blue-800 border border-blue-200{% endif %}">
          {{ message }}
        </div>
        {% endfor %}
      </div>
      {% endif %}
      {% block content %}{% endblock %}
    </div>
  </main>
</div>

{% else %}
{% block auth_content %}{% endblock %}
{% endif %}

</body>
</html>
''')

# ══════════════════════════════════════════════════════════════════
# ACCOUNTS TEMPLATES
# ══════════════════════════════════════════════════════════════════
write('templates/accounts/login.html', '''{% extends "base.html" %}
{% block auth_content %}
<div class="min-h-screen flex items-center justify-center bg-gray-50">
  <div class="w-full max-w-md">
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900">&#x1F4CB; CLRT</h1>
      <p class="text-gray-500 mt-1">Client Lifecycle & Revenue Tracker</p>
    </div>
    <div class="card p-8">
      <h2 class="text-xl font-semibold text-gray-800 mb-6">Sign in to your account</h2>
      {% if messages %}
        {% for message in messages %}
        <div class="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{{ message }}</div>
        {% endfor %}
      {% endif %}
      {% if form.non_field_errors %}
        <div class="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-sm border border-red-200">{{ form.non_field_errors }}</div>
      {% endif %}
      <form method="post" class="space-y-4">
        {% csrf_token %}
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input type="text" name="username" class="input" placeholder="Enter username" autofocus required />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input type="password" name="password" class="input" placeholder="Enter password" required />
        </div>
        <button type="submit" class="btn-primary w-full justify-center py-2.5">Sign In</button>
      </form>
    </div>
  </div>
</div>
{% endblock %}
''')

write('templates/accounts/profile.html', '''{% extends "base.html" %}
{% block title %}Profile{% endblock %}
{% block nav_dashboard %}{% endblock %}
{% block content %}
<div class="max-w-lg">
  <h1 class="text-2xl font-bold text-gray-900 mb-6">My Profile</h1>
  <div class="card p-6 space-y-4">
    <div class="flex items-center gap-4">
      <div class="w-14 h-14 rounded-full bg-blue-600 flex items-center justify-center text-white text-xl font-bold">
        {{ user.username|slice:":2"|upper }}
      </div>
      <div>
        <p class="text-lg font-semibold">{{ user.get_full_name|default:user.username }}</p>
        <p class="text-gray-500 text-sm">{{ user.get_role_display }}</p>
      </div>
    </div>
    <div class="border-t pt-4 grid grid-cols-2 gap-4 text-sm">
      <div><span class="text-gray-500">Username</span><p class="font-medium">{{ user.username }}</p></div>
      <div><span class="text-gray-500">Email</span><p class="font-medium">{{ user.email|default:"—" }}</p></div>
      <div><span class="text-gray-500">Role</span><p class="font-medium">{{ user.get_role_display }}</p></div>
      <div><span class="text-gray-500">Joined</span><p class="font-medium">{{ user.date_joined|date:"M d, Y" }}</p></div>
    </div>
  </div>
</div>
{% endblock %}
''')

write('templates/accounts/user_list.html', '''{% extends "base.html" %}
{% block title %}Users{% endblock %}
{% block nav_users %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="flex items-center justify-between mb-6">
  <h1 class="text-2xl font-bold text-gray-900">Users</h1>
  <a href="{% url "accounts:user_create" %}" class="btn-primary">+ Add User</a>
</div>
<div class="card overflow-hidden">
  <table class="w-full text-sm">
    <thead class="bg-gray-50 border-b border-gray-200">
      <tr>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Name</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Username</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Role</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Status</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      {% for u in users %}
      <tr class="hover:bg-gray-50">
        <td class="px-4 py-3 font-medium">{{ u.get_full_name|default:u.username }}</td>
        <td class="px-4 py-3 text-gray-500">{{ u.username }}</td>
        <td class="px-4 py-3"><span class="badge bg-blue-100 text-blue-800">{{ u.get_role_display }}</span></td>
        <td class="px-4 py-3">
          {% if u.is_active %}<span class="badge bg-green-100 text-green-800">Active</span>
          {% else %}<span class="badge bg-gray-100 text-gray-600">Inactive</span>{% endif %}
        </td>
      </tr>
      {% empty %}
      <tr><td colspan="4" class="px-4 py-8 text-center text-gray-400">No users found.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
''')

write('templates/accounts/user_form.html', '''{% extends "base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block content %}
<div class="max-w-lg">
  <h1 class="text-2xl font-bold text-gray-900 mb-6">{{ title }}</h1>
  <div class="card p-6">
    <form method="post" class="space-y-4">
      {% csrf_token %}
      {% for field in form %}
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">{{ field.label }}</label>
        {{ field }}
        {% if field.errors %}<p class="text-red-600 text-xs mt-1">{{ field.errors.0 }}</p>{% endif %}
      </div>
      {% endfor %}
      <div class="flex gap-3 pt-2">
        <button type="submit" class="btn-primary">Save</button>
        <a href="{% url "accounts:user_list" %}" class="btn-secondary">Cancel</a>
      </div>
    </form>
  </div>
</div>
{% endblock %}
''')

# ══════════════════════════════════════════════════════════════════
# DASHBOARD TEMPLATE
# ══════════════════════════════════════════════════════════════════
write('templates/dashboard/dashboard.html', '''{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block nav_dashboard %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="mb-6">
  <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
  <p class="text-gray-500 text-sm">{{ today|date:"l, F j, Y" }}</p>
</div>

<!-- Stats Row -->
<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
  <div class="card p-4">
    <p class="text-xs text-gray-500 mb-1">Total Leads</p>
    <p class="text-3xl font-bold text-gray-900">{{ lead_stats.total }}</p>
    <p class="text-xs text-green-600 mt-1">{{ lead_stats.won }} won · {{ lead_stats.new }} new</p>
  </div>
  <div class="card p-4 {% if todays_followups %}border-blue-300{% endif %}">
    <p class="text-xs text-gray-500 mb-1">Follow-ups Today</p>
    <p class="text-3xl font-bold {% if todays_followups %}text-blue-600{% else %}text-gray-900{% endif %}">{{ todays_followups|length }}</p>
    <p class="text-xs text-gray-400 mt-1">Scheduled for today</p>
  </div>
  <div class="card p-4 {% if overdue_followups %}border-orange-300{% endif %}">
    <p class="text-xs text-gray-500 mb-1">Overdue Follow-ups</p>
    <p class="text-3xl font-bold {% if overdue_followups %}text-orange-600{% else %}text-gray-900{% endif %}">{{ overdue_followups|length }}</p>
    <p class="text-xs text-gray-400 mt-1">Missed follow-ups</p>
  </div>
  <div class="card p-4">
    <p class="text-xs text-gray-500 mb-1">Revenue This Month</p>
    <p class="text-2xl font-bold text-green-600">Rs. {{ revenue_month|floatformat:0 }}</p>
    <p class="text-xs text-gray-400 mt-1">Paid invoices</p>
  </div>
</div>

<div class="grid lg:grid-cols-2 gap-6">
  <!-- Today's Follow-ups -->
  <div class="card">
    <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
      <h2 class="font-semibold text-gray-900">&#x1F4C5; Today\'s Follow-ups</h2>
      <a href="/leads/?followup=today" class="text-xs text-blue-600 hover:underline">View all</a>
    </div>
    <ul class="divide-y divide-gray-50">
      {% for a in todays_followups %}
      <li class="px-5 py-3 flex items-center justify-between">
        <div>
          <a href="{% url "leads:lead_detail" a.lead.pk %}" class="font-medium text-sm text-gray-900 hover:text-blue-600">{{ a.lead.organization_name }}</a>
          <p class="text-xs text-gray-400">{{ a.get_type_display }}</p>
        </div>
        <span class="badge bg-blue-100 text-blue-700">Today</span>
      </li>
      {% empty %}
      <li class="px-5 py-8 text-center text-sm text-gray-400">No follow-ups scheduled today &#x2705;</li>
      {% endfor %}
    </ul>
  </div>

  <!-- Overdue Follow-ups -->
  <div class="card">
    <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
      <h2 class="font-semibold text-gray-900">&#x26A0;&#xFE0F; Overdue Follow-ups</h2>
    </div>
    <ul class="divide-y divide-gray-50">
      {% for a in overdue_followups|slice:":8" %}
      <li class="px-5 py-3 flex items-center justify-between">
        <div>
          <a href="{% url "leads:lead_detail" a.lead.pk %}" class="font-medium text-sm text-gray-900 hover:text-blue-600">{{ a.lead.organization_name }}</a>
          <p class="text-xs text-gray-400">Due: {{ a.next_follow_up_date }}</p>
        </div>
        <span class="badge bg-red-100 text-red-700">Overdue</span>
      </li>
      {% empty %}
      <li class="px-5 py-8 text-center text-sm text-gray-400">No overdue follow-ups &#x2705;</li>
      {% endfor %}
    </ul>
  </div>

  <!-- Expiring Contracts -->
  <div class="card">
    <div class="px-5 py-4 border-b border-gray-100">
      <h2 class="font-semibold text-gray-900">&#x1F4C3; Contracts Expiring Soon (30 days)</h2>
    </div>
    <ul class="divide-y divide-gray-50">
      {% for c in expiring_contracts %}
      <li class="px-5 py-3 flex items-center justify-between">
        <div>
          <a href="{% url "clients:contract_detail" c.pk %}" class="font-medium text-sm text-gray-900 hover:text-blue-600">{{ c.contract_title }}</a>
          <p class="text-xs text-gray-400">{{ c.client }} · expires {{ c.end_date }}</p>
        </div>
        <span class="badge bg-yellow-100 text-yellow-800">{{ c.days_until_expiry }}d left</span>
      </li>
      {% empty %}
      <li class="px-5 py-8 text-center text-sm text-gray-400">No contracts expiring soon &#x2705;</li>
      {% endfor %}
    </ul>
  </div>

  <!-- Pending Invoices -->
  <div class="card">
    <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
      <h2 class="font-semibold text-gray-900">&#x1F4B3; Pending Invoices</h2>
      <a href="/billing/?status=overdue" class="text-xs text-red-600 hover:underline">View overdue</a>
    </div>
    <ul class="divide-y divide-gray-50">
      {% for inv in pending_invoices|slice:":8" %}
      <li class="px-5 py-3 flex items-center justify-between">
        <div>
          <a href="{% url "billing:invoice_detail" inv.pk %}" class="font-medium text-sm text-gray-900 hover:text-blue-600">{{ inv.invoice_number }}</a>
          <p class="text-xs text-gray-400">{{ inv.client }} · Rs. {{ inv.amount|floatformat:0 }} · due {{ inv.due_date }}</p>
        </div>
        <span class="badge {% if inv.status == "overdue" %}bg-red-100 text-red-700{% else %}bg-yellow-100 text-yellow-800{% endif %}">
          {{ inv.get_status_display }}
        </span>
      </li>
      {% empty %}
      <li class="px-5 py-8 text-center text-sm text-gray-400">No pending invoices &#x2705;</li>
      {% endfor %}
    </ul>
  </div>
</div>
{% endblock %}
''')

# ══════════════════════════════════════════════════════════════════
# LEADS TEMPLATES
# ══════════════════════════════════════════════════════════════════
STATUS_BADGE = {
    'new': 'bg-gray-100 text-gray-700',
    'contacted': 'bg-blue-100 text-blue-700',
    'demo': 'bg-purple-100 text-purple-700',
    'negotiation': 'bg-yellow-100 text-yellow-800',
    'won': 'bg-green-100 text-green-700',
    'lost': 'bg-red-100 text-red-700',
}

write('templates/leads/lead_list.html', '''{% extends "base.html" %}
{% block title %}Leads{% endblock %}
{% block nav_leads %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="flex items-center justify-between mb-6">
  <h1 class="text-2xl font-bold text-gray-900">Leads</h1>
  {% if user.role in "admin,sales" or user.is_superuser %}
  <a href="{% url "leads:lead_create" %}" class="btn-primary">+ Add Lead</a>
  {% endif %}
</div>

<!-- Filters -->
<form method="get" class="flex gap-3 mb-5">
  <input type="text" name="q" value="{{ q }}" placeholder="Search organization, contact, phone…" class="input max-w-xs" />
  <select name="status" class="input max-w-[160px]">
    <option value="">All Status</option>
    {% for val, label in status_choices %}
    <option value="{{ val }}" {% if status == val %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
  </select>
  <button type="submit" class="btn-secondary">Filter</button>
  {% if q or status %}<a href="/leads/" class="btn-secondary">Clear</a>{% endif %}
</form>

<div class="card overflow-hidden">
  <table class="w-full text-sm">
    <thead class="bg-gray-50 border-b border-gray-200">
      <tr>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Organization</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Contact</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Phone</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Status</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Assigned To</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Added</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      {% for lead in leads %}
      <tr class="hover:bg-gray-50 cursor-pointer" onclick="location.href=\'{% url "leads:lead_detail" lead.pk %}\'">
        <td class="px-4 py-3 font-medium text-gray-900">{{ lead.organization_name }}</td>
        <td class="px-4 py-3 text-gray-600">{{ lead.contact_person }}</td>
        <td class="px-4 py-3 text-gray-500">{{ lead.phone }}</td>
        <td class="px-4 py-3">
          <span class="badge
            {% if lead.status == "new" %}bg-gray-100 text-gray-700
            {% elif lead.status == "contacted" %}bg-blue-100 text-blue-700
            {% elif lead.status == "demo" %}bg-purple-100 text-purple-700
            {% elif lead.status == "negotiation" %}bg-yellow-100 text-yellow-800
            {% elif lead.status == "won" %}bg-green-100 text-green-700
            {% elif lead.status == "lost" %}bg-red-100 text-red-700
            {% endif %}">{{ lead.get_status_display }}</span>
        </td>
        <td class="px-4 py-3 text-gray-500">{{ lead.assigned_to|default:"—" }}</td>
        <td class="px-4 py-3 text-gray-400">{{ lead.created_at|date:"M d, Y" }}</td>
      </tr>
      {% empty %}
      <tr><td colspan="6" class="px-4 py-10 text-center text-gray-400">No leads found. <a href="{% url "leads:lead_create" %}" class="text-blue-600 hover:underline">Add your first lead.</a></td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
''')

write('templates/leads/lead_detail.html', '''{% extends "base.html" %}
{% block title %}{{ lead.organization_name }}{% endblock %}
{% block nav_leads %}bg-gray-800 text-white{% endblock %}
{% block content %}
<!-- Header -->
<div class="flex items-start justify-between mb-6">
  <div>
    <div class="flex items-center gap-3 mb-1">
      <h1 class="text-2xl font-bold text-gray-900">{{ lead.organization_name }}</h1>
      <span class="badge
        {% if lead.status == "new" %}bg-gray-100 text-gray-700
        {% elif lead.status == "contacted" %}bg-blue-100 text-blue-700
        {% elif lead.status == "demo" %}bg-purple-100 text-purple-700
        {% elif lead.status == "negotiation" %}bg-yellow-100 text-yellow-800
        {% elif lead.status == "won" %}bg-green-100 text-green-700
        {% elif lead.status == "lost" %}bg-red-100 text-red-700
        {% endif %}">{{ lead.get_status_display }}</span>
    </div>
    <p class="text-gray-500">{{ lead.contact_person }} · {{ lead.phone }} {% if lead.email %}· {{ lead.email }}{% endif %}</p>
  </div>
  <div class="flex gap-2">
    {% if lead.is_won %}
      {% if lead.client %}
      <a href="{% url "clients:client_detail" lead.client.pk %}" class="btn-secondary">View Client</a>
      {% else %}
      <a href="{% url "leads:convert_to_client" lead.pk %}" class="btn-primary">Convert to Client</a>
      {% endif %}
    {% endif %}
    <a href="{% url "leads:lead_edit" lead.pk %}" class="btn-secondary">Edit</a>
    {% if user.is_admin %}
    <a href="{% url "leads:lead_delete" lead.pk %}" class="btn-danger">Delete</a>
    {% endif %}
  </div>
</div>

<div class="grid lg:grid-cols-3 gap-6">
  <!-- Lead Info -->
  <div class="card p-5 space-y-3">
    <h3 class="font-semibold text-gray-900">Lead Details</h3>
    {% if lead.notes %}
    <div>
      <p class="text-xs text-gray-400 mb-0.5">Notes</p>
      <p class="text-sm text-gray-700">{{ lead.notes }}</p>
    </div>
    {% endif %}
    <div>
      <p class="text-xs text-gray-400 mb-0.5">Assigned To</p>
      <p class="text-sm font-medium">{{ lead.assigned_to|default:"Unassigned" }}</p>
    </div>
    <div>
      <p class="text-xs text-gray-400 mb-0.5">Created</p>
      <p class="text-sm">{{ lead.created_at|date:"M d, Y" }}</p>
    </div>
  </div>

  <!-- Activity Timeline -->
  <div class="lg:col-span-2">
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold text-gray-900">Activity Log</h3>
      <a href="{% url "leads:activity_add" lead.pk %}" class="btn-primary text-xs">+ Log Activity</a>
    </div>
    <div class="space-y-3">
      {% for activity in activities %}
      <div class="card p-4">
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xs font-bold flex-shrink-0">
            {% if activity.type == "call" %}&#x260E;
            {% elif activity.type == "meeting" %}&#x1F91D;
            {% elif activity.type == "follow_up" %}&#x1F504;
            {% else %}&#x2709;{% endif %}
          </div>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-900">{{ activity.get_type_display }}</span>
              <span class="text-xs text-gray-400">{{ activity.created_at|date:"M d, Y H:i" }}</span>
            </div>
            <p class="text-sm text-gray-600 mt-1">{{ activity.notes }}</p>
            {% if activity.next_follow_up_date %}
            <p class="text-xs text-blue-600 mt-1">&#x1F4C5; Next follow-up: {{ activity.next_follow_up_date }}</p>
            {% endif %}
            {% if activity.created_by %}
            <p class="text-xs text-gray-400 mt-1">by {{ activity.created_by.get_full_name|default:activity.created_by.username }}</p>
            {% endif %}
          </div>
        </div>
      </div>
      {% empty %}
      <div class="card p-8 text-center text-gray-400">
        <p>No activities logged yet.</p>
        <a href="{% url "leads:activity_add" lead.pk %}" class="text-blue-600 hover:underline text-sm mt-1 inline-block">Log first activity</a>
      </div>
      {% endfor %}
    </div>
  </div>
</div>
{% endblock %}
''')

write('templates/leads/lead_form.html', '''{% extends "base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block nav_leads %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="max-w-2xl">
  <div class="flex items-center gap-3 mb-6">
    <a href="/leads/" class="text-gray-400 hover:text-gray-600">&#x2190; Leads</a>
    <h1 class="text-2xl font-bold text-gray-900">{{ title }}</h1>
  </div>
  <div class="card p-6">
    <form method="post" class="space-y-4">
      {% csrf_token %}
      <div class="grid grid-cols-2 gap-4">
        <div class="col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-1">Organization Name *</label>
          <input type="text" name="organization_name" value="{{ form.organization_name.value|default:"" }}" class="input" required autofocus />
          {% if form.organization_name.errors %}<p class="text-red-600 text-xs mt-1">{{ form.organization_name.errors.0 }}</p>{% endif %}
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Contact Person *</label>
          <input type="text" name="contact_person" value="{{ form.contact_person.value|default:"" }}" class="input" required />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Phone *</label>
          <input type="text" name="phone" value="{{ form.phone.value|default:"" }}" class="input" required />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input type="email" name="email" value="{{ form.email.value|default:"" }}" class="input" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select name="status" class="input">
            {% for val, label in form.fields.status.choices %}
            <option value="{{ val }}" {% if form.status.value == val %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-1">Assigned To</label>
          <select name="assigned_to" class="input">
            <option value="">— Unassigned —</option>
            {% for u in form.fields.assigned_to.queryset %}
            <option value="{{ u.pk }}" {% if form.assigned_to.value|stringformat:"s" == u.pk|stringformat:"s" %}selected{% endif %}>{{ u }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-1">Notes</label>
          <textarea name="notes" rows="3" class="input">{{ form.notes.value|default:"" }}</textarea>
        </div>
      </div>
      <div class="flex gap-3 pt-2">
        <button type="submit" class="btn-primary">Save Lead</button>
        <a href="/leads/" class="btn-secondary">Cancel</a>
      </div>
    </form>
  </div>
</div>
{% endblock %}
''')

write('templates/leads/activity_form.html', '''{% extends "base.html" %}
{% block title %}Log Activity{% endblock %}
{% block nav_leads %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="max-w-lg">
  <div class="flex items-center gap-3 mb-6">
    <a href="{% url "leads:lead_detail" lead.pk %}" class="text-gray-400 hover:text-gray-600">&#x2190; {{ lead.organization_name }}</a>
    <h1 class="text-2xl font-bold text-gray-900">Log Activity</h1>
  </div>
  <div class="card p-6">
    <form method="post" class="space-y-4">
      {% csrf_token %}
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
        <select name="type" class="input">
          {% for val, label in form.fields.type.choices %}
          <option value="{{ val }}" {% if form.type.value == val %}selected{% endif %}>{{ label }}</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Notes *</label>
        <textarea name="notes" rows="4" class="input" required placeholder="What happened? What was discussed?">{{ form.notes.value|default:"" }}</textarea>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Next Follow-up Date</label>
        <input type="date" name="next_follow_up_date" value="{{ form.next_follow_up_date.value|default:"" }}" class="input" />
      </div>
      <div class="flex gap-3 pt-2">
        <button type="submit" class="btn-primary">Save Activity</button>
        <a href="{% url "leads:lead_detail" lead.pk %}" class="btn-secondary">Cancel</a>
      </div>
    </form>
  </div>
</div>
{% endblock %}
''')

write('templates/leads/lead_confirm_delete.html', '''{% extends "base.html" %}
{% block title %}Delete Lead{% endblock %}
{% block content %}
<div class="max-w-md">
  <div class="card p-6 text-center">
    <div class="text-red-500 text-5xl mb-4">&#x26A0;&#xFE0F;</div>
    <h2 class="text-xl font-bold text-gray-900 mb-2">Delete Lead?</h2>
    <p class="text-gray-500 mb-6">This will permanently delete <strong>{{ lead.organization_name }}</strong> and all associated activities.</p>
    <div class="flex gap-3 justify-center">
      <form method="post">
        {% csrf_token %}
        <button type="submit" class="btn-danger">Yes, Delete</button>
      </form>
      <a href="{% url "leads:lead_detail" lead.pk %}" class="btn-secondary">Cancel</a>
    </div>
  </div>
</div>
{% endblock %}
''')

write('templates/leads/convert_confirm.html', '''{% extends "base.html" %}
{% block title %}Convert to Client{% endblock %}
{% block content %}
<div class="max-w-md">
  <div class="card p-6 text-center">
    <div class="text-green-500 text-5xl mb-4">&#x1F389;</div>
    <h2 class="text-xl font-bold text-gray-900 mb-2">Convert to Client</h2>
    <p class="text-gray-500 mb-6">Convert <strong>{{ lead.organization_name }}</strong> from a Won Lead into a Client record.</p>
    <div class="flex gap-3 justify-center">
      <form method="post">
        {% csrf_token %}
        <button type="submit" class="btn-primary">Convert</button>
      </form>
      <a href="{% url "leads:lead_detail" lead.pk %}" class="btn-secondary">Cancel</a>
    </div>
  </div>
</div>
{% endblock %}
''')

# ══════════════════════════════════════════════════════════════════
# CLIENTS TEMPLATES
# ══════════════════════════════════════════════════════════════════
write('templates/clients/client_list.html', '''{% extends "base.html" %}
{% block title %}Clients{% endblock %}
{% block nav_clients %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="flex items-center justify-between mb-6">
  <h1 class="text-2xl font-bold text-gray-900">Clients</h1>
  {% if user.is_admin or user.is_accounts %}
  <a href="{% url "clients:client_create" %}" class="btn-primary">+ Add Client</a>
  {% endif %}
</div>
<form method="get" class="flex gap-3 mb-5">
  <input type="text" name="q" value="{{ q }}" placeholder="Search clients…" class="input max-w-xs" />
  <button type="submit" class="btn-secondary">Search</button>
  {% if q %}<a href="/clients/" class="btn-secondary">Clear</a>{% endif %}
</form>
<div class="card overflow-hidden">
  <table class="w-full text-sm">
    <thead class="bg-gray-50 border-b border-gray-200">
      <tr>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Organization</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Email</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Phone</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Contracts</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Since</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      {% for client in clients %}
      <tr class="hover:bg-gray-50 cursor-pointer" onclick="location.href=\'{% url "clients:client_detail" client.pk %}\'">
        <td class="px-4 py-3 font-medium text-gray-900">{{ client.organization_name }}</td>
        <td class="px-4 py-3 text-gray-500">{{ client.email|default:"—" }}</td>
        <td class="px-4 py-3 text-gray-500">{{ client.phone|default:"—" }}</td>
        <td class="px-4 py-3"><span class="badge bg-gray-100 text-gray-700">{{ client.contracts.count }}</span></td>
        <td class="px-4 py-3 text-gray-400">{{ client.created_at|date:"M Y" }}</td>
      </tr>
      {% empty %}
      <tr><td colspan="5" class="px-4 py-10 text-center text-gray-400">No clients yet.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
''')

write('templates/clients/client_detail.html', '''{% extends "base.html" %}
{% block title %}{{ client.organization_name }}{% endblock %}
{% block nav_clients %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="flex items-start justify-between mb-6">
  <div>
    <h1 class="text-2xl font-bold text-gray-900">{{ client.organization_name }}</h1>
    {% if client.email %}<p class="text-gray-500 text-sm">{{ client.email }}{% if client.phone %} · {{ client.phone }}{% endif %}</p>{% endif %}
    {% if client.linked_lead %}<p class="text-xs text-blue-600 mt-1">&#x1F517; From lead: <a href="{% url "leads:lead_detail" client.linked_lead.pk %}" class="hover:underline">{{ client.linked_lead.organization_name }}</a></p>{% endif %}
  </div>
  <div class="flex gap-2">
    <a href="{% url "clients:contract_create" client.pk %}" class="btn-primary">+ Add Contract</a>
    <a href="{% url "clients:client_edit" client.pk %}" class="btn-secondary">Edit</a>
  </div>
</div>

<h2 class="font-semibold text-gray-900 mb-3">Contracts</h2>
<div class="space-y-3">
  {% for contract in contracts %}
  <div class="card p-5 flex items-center justify-between">
    <div>
      <a href="{% url "clients:contract_detail" contract.pk %}" class="font-medium text-gray-900 hover:text-blue-600">{{ contract.contract_title }}</a>
      <p class="text-xs text-gray-400 mt-0.5">{{ contract.start_date }} → {{ contract.end_date }} · {{ contract.get_billing_cycle_display }} · Rs. {{ contract.contract_value|floatformat:0 }}</p>
    </div>
    <div class="flex items-center gap-3">
      {% if contract.is_expiring_soon %}<span class="badge bg-yellow-100 text-yellow-800">Expiring in {{ contract.days_until_expiry }}d</span>{% endif %}
      <span class="badge {% if contract.status == "active" %}bg-green-100 text-green-700{% else %}bg-red-100 text-red-700{% endif %}">{{ contract.get_status_display }}</span>
    </div>
  </div>
  {% empty %}
  <div class="card p-8 text-center text-gray-400">No contracts yet. <a href="{% url "clients:contract_create" client.pk %}" class="text-blue-600 hover:underline">Add first contract.</a></div>
  {% endfor %}
</div>

<!-- Invoices -->
<h2 class="font-semibold text-gray-900 mt-8 mb-3">Recent Invoices</h2>
<div class="card overflow-hidden">
  <table class="w-full text-sm">
    <thead class="bg-gray-50 border-b">
      <tr>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Invoice #</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Amount</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Due Date</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Status</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      {% for inv in client.invoices.all|slice:":10" %}
      <tr class="hover:bg-gray-50 cursor-pointer" onclick="location.href=\'{% url "billing:invoice_detail" inv.pk %}\'">
        <td class="px-4 py-3 font-medium">{{ inv.invoice_number }}</td>
        <td class="px-4 py-3">Rs. {{ inv.amount|floatformat:0 }}</td>
        <td class="px-4 py-3 text-gray-500">{{ inv.due_date }}</td>
        <td class="px-4 py-3"><span class="badge {% if inv.status == "paid" %}bg-green-100 text-green-700{% elif inv.status == "overdue" %}bg-red-100 text-red-700{% else %}bg-yellow-100 text-yellow-800{% endif %}">{{ inv.get_status_display }}</span></td>
      </tr>
      {% empty %}
      <tr><td colspan="4" class="px-4 py-6 text-center text-gray-400">No invoices.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
''')

write('templates/clients/client_form.html', '''{% extends "base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block nav_clients %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="max-w-lg">
  <div class="flex items-center gap-3 mb-6">
    <a href="/clients/" class="text-gray-400 hover:text-gray-600">&#x2190; Clients</a>
    <h1 class="text-2xl font-bold text-gray-900">{{ title }}</h1>
  </div>
  <div class="card p-6">
    <form method="post" class="space-y-4">
      {% csrf_token %}
      {% for field in form %}
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">{{ field.label }}</label>
        {{ field }}
        {% if field.errors %}<p class="text-red-600 text-xs mt-1">{{ field.errors.0 }}</p>{% endif %}
      </div>
      {% endfor %}
      <div class="flex gap-3 pt-2">
        <button type="submit" class="btn-primary">Save</button>
        <a href="/clients/" class="btn-secondary">Cancel</a>
      </div>
    </form>
  </div>
</div>
{% endblock %}
''')

write('templates/clients/contract_form.html', '''{% extends "base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block nav_clients %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="max-w-2xl">
  <div class="flex items-center gap-3 mb-6">
    <a href="{% url "clients:client_detail" client.pk %}" class="text-gray-400 hover:text-gray-600">&#x2190; {{ client.organization_name }}</a>
    <h1 class="text-2xl font-bold text-gray-900">{{ title }}</h1>
  </div>
  <div class="card p-6">
    <form method="post" enctype="multipart/form-data" class="space-y-4">
      {% csrf_token %}
      <div class="grid grid-cols-2 gap-4">
        <div class="col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-1">Contract Title *</label>
          <input type="text" name="contract_title" value="{{ form.contract_title.value|default:"" }}" class="input" required />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Start Date *</label>
          <input type="date" name="start_date" value="{{ form.start_date.value|default:"" }}" class="input" required />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">End Date *</label>
          <input type="date" name="end_date" value="{{ form.end_date.value|default:"" }}" class="input" required />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Billing Cycle</label>
          <select name="billing_cycle" class="input">
            {% for val, label in form.fields.billing_cycle.choices %}
            <option value="{{ val }}" {% if form.billing_cycle.value == val %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Contract Value (Rs.) *</label>
          <input type="number" step="0.01" name="contract_value" value="{{ form.contract_value.value|default:"" }}" class="input" required />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select name="status" class="input">
            {% for val, label in form.fields.status.choices %}
            <option value="{{ val }}" {% if form.status.value == val %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Contract Document (PDF/Image)</label>
          <input type="file" name="document" class="input" accept=".pdf,.png,.jpg,.jpeg" />
          {% if form.instance.document %}<p class="text-xs text-gray-400 mt-1">Current: <a href="{{ form.instance.document.url }}" class="text-blue-600" target="_blank">View</a></p>{% endif %}
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium text-gray-700 mb-1">Notes</label>
          <textarea name="notes" rows="3" class="input">{{ form.notes.value|default:"" }}</textarea>
        </div>
      </div>
      <div class="flex gap-3 pt-2">
        <button type="submit" class="btn-primary">Save Contract</button>
        <a href="{% url "clients:client_detail" client.pk %}" class="btn-secondary">Cancel</a>
      </div>
    </form>
  </div>
</div>
{% endblock %}
''')

write('templates/clients/contract_detail.html', '''{% extends "base.html" %}
{% block title %}{{ contract.contract_title }}{% endblock %}
{% block nav_clients %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="flex items-start justify-between mb-6">
  <div>
    <div class="flex items-center gap-3 mb-1">
      <h1 class="text-2xl font-bold text-gray-900">{{ contract.contract_title }}</h1>
      <span class="badge {% if contract.status == "active" %}bg-green-100 text-green-700{% else %}bg-red-100 text-red-700{% endif %}">{{ contract.get_status_display }}</span>
      {% if contract.is_expiring_soon %}<span class="badge bg-yellow-100 text-yellow-800">&#x26A0; Expiring in {{ contract.days_until_expiry }} days</span>{% endif %}
    </div>
    <a href="{% url "clients:client_detail" contract.client.pk %}" class="text-blue-600 hover:underline text-sm">{{ contract.client.organization_name }}</a>
  </div>
  <a href="{% url "clients:contract_edit" contract.pk %}" class="btn-secondary">Edit</a>
</div>

<div class="grid lg:grid-cols-2 gap-6">
  <div class="card p-5 space-y-4">
    <h3 class="font-semibold text-gray-900">Contract Details</h3>
    <div class="grid grid-cols-2 gap-4 text-sm">
      <div><p class="text-gray-400 text-xs">Start Date</p><p class="font-medium">{{ contract.start_date }}</p></div>
      <div><p class="text-gray-400 text-xs">End Date</p><p class="font-medium">{{ contract.end_date }}</p></div>
      <div><p class="text-gray-400 text-xs">Billing Cycle</p><p class="font-medium">{{ contract.get_billing_cycle_display }}</p></div>
      <div><p class="text-gray-400 text-xs">Contract Value</p><p class="font-bold text-gray-900">Rs. {{ contract.contract_value|floatformat:0 }}</p></div>
    </div>
    {% if contract.notes %}<div><p class="text-gray-400 text-xs">Notes</p><p class="text-sm">{{ contract.notes }}</p></div>{% endif %}
    {% if contract.document %}
    <a href="{{ contract.document.url }}" target="_blank" class="btn-secondary inline-flex items-center gap-2">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
      View Document
    </a>
    {% endif %}
  </div>
</div>
{% endblock %}
''')

# ══════════════════════════════════════════════════════════════════
# BILLING TEMPLATES
# ══════════════════════════════════════════════════════════════════
write('templates/billing/invoice_list.html', '''{% extends "base.html" %}
{% block title %}Billing{% endblock %}
{% block nav_billing %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="flex items-center justify-between mb-6">
  <h1 class="text-2xl font-bold text-gray-900">Invoices</h1>
  <div class="flex gap-2">
    <form method="post" action="{% url "billing:mark_overdue" %}">{% csrf_token %}<button type="submit" class="btn-secondary text-xs">Mark Overdue</button></form>
    {% if user.role in "admin,accounts" or user.is_superuser %}
    <a href="{% url "billing:invoice_create" %}" class="btn-primary">+ New Invoice</a>
    {% endif %}
  </div>
</div>

<form method="get" class="flex gap-3 mb-5">
  <input type="text" name="q" value="{{ q }}" placeholder="Search invoice #, client…" class="input max-w-xs" />
  <select name="status" class="input max-w-[160px]">
    <option value="">All Status</option>
    {% for val, label in status_choices %}
    <option value="{{ val }}" {% if status == val %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
  </select>
  <button type="submit" class="btn-secondary">Filter</button>
  {% if q or status %}<a href="/billing/" class="btn-secondary">Clear</a>{% endif %}
</form>

<div class="card overflow-hidden">
  <table class="w-full text-sm">
    <thead class="bg-gray-50 border-b border-gray-200">
      <tr>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Invoice #</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Client</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Amount</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Due Date</th>
        <th class="px-4 py-3 text-left font-medium text-gray-500">Status</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
      {% for inv in invoices %}
      <tr class="hover:bg-gray-50 cursor-pointer" onclick="location.href=\'{% url "billing:invoice_detail" inv.pk %}\'">
        <td class="px-4 py-3 font-medium text-blue-600">{{ inv.invoice_number }}</td>
        <td class="px-4 py-3 text-gray-700">{{ inv.client }}</td>
        <td class="px-4 py-3 font-medium">Rs. {{ inv.amount|floatformat:0 }}</td>
        <td class="px-4 py-3 text-gray-500 {% if inv.is_overdue %}text-red-600 font-medium{% endif %}">{{ inv.due_date }}</td>
        <td class="px-4 py-3">
          <span class="badge
            {% if inv.status == "paid" %}bg-green-100 text-green-700
            {% elif inv.status == "overdue" %}bg-red-100 text-red-700
            {% elif inv.status == "pending" %}bg-yellow-100 text-yellow-800
            {% else %}bg-gray-100 text-gray-600{% endif %}">{{ inv.get_status_display }}</span>
        </td>
      </tr>
      {% empty %}
      <tr><td colspan="5" class="px-4 py-10 text-center text-gray-400">No invoices found.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
''')

write('templates/billing/invoice_detail.html', '''{% extends "base.html" %}
{% block title %}{{ invoice.invoice_number }}{% endblock %}
{% block nav_billing %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="flex items-start justify-between mb-6">
  <div>
    <div class="flex items-center gap-3 mb-1">
      <h1 class="text-2xl font-bold text-gray-900">{{ invoice.invoice_number }}</h1>
      <span class="badge
        {% if invoice.status == "paid" %}bg-green-100 text-green-700
        {% elif invoice.status == "overdue" %}bg-red-100 text-red-700
        {% elif invoice.status == "pending" %}bg-yellow-100 text-yellow-800
        {% else %}bg-gray-100 text-gray-600{% endif %}">{{ invoice.get_status_display }}</span>
    </div>
    <a href="{% url "clients:client_detail" invoice.client.pk %}" class="text-blue-600 hover:underline text-sm">{{ invoice.client }}</a>
    {% if invoice.contract %} · <a href="{% url "clients:contract_detail" invoice.contract.pk %}" class="text-blue-600 hover:underline text-sm">{{ invoice.contract.contract_title }}</a>{% endif %}
  </div>
  <div class="flex gap-2">
    {% if invoice.status != "paid" %}
    <a href="{% url "billing:payment_add" invoice.pk %}" class="btn-primary">+ Record Payment</a>
    {% endif %}
    <a href="{% url "billing:invoice_edit" invoice.pk %}" class="btn-secondary">Edit</a>
  </div>
</div>

<div class="grid lg:grid-cols-2 gap-6">
  <div class="card p-5">
    <h3 class="font-semibold text-gray-900 mb-4">Invoice Details</h3>
    <div class="space-y-3 text-sm">
      <div class="flex justify-between"><span class="text-gray-400">Invoice Total</span><span class="font-bold text-lg">Rs. {{ invoice.amount|floatformat:0 }}</span></div>
      <div class="flex justify-between"><span class="text-gray-400">Due Date</span><span class="{% if invoice.is_overdue %}text-red-600 font-medium{% endif %}">{{ invoice.due_date }}</span></div>
      <div class="flex justify-between"><span class="text-gray-400">Generated</span><span>{{ invoice.generated_date }}</span></div>
      {% if invoice.description %}<div><p class="text-gray-400 text-xs mb-1">Description</p><p>{{ invoice.description }}</p></div>{% endif %}
      <div class="border-t pt-3">
        <div class="flex justify-between"><span class="text-gray-400">Paid</span><span class="text-green-600 font-medium">Rs. {{ paid_total|floatformat:0 }}</span></div>
        <div class="flex justify-between mt-1"><span class="text-gray-700 font-medium">Balance Due</span><span class="font-bold {% if balance > 0 %}text-red-600{% else %}text-green-600{% endif %}">Rs. {{ balance|floatformat:0 }}</span></div>
      </div>
    </div>
  </div>

  <div>
    <h3 class="font-semibold text-gray-900 mb-3">Payment History</h3>
    <div class="space-y-2">
      {% for p in payments %}
      <div class="card p-4 flex items-center justify-between">
        <div>
          <p class="text-sm font-medium">Rs. {{ p.amount_paid|floatformat:0 }}</p>
          <p class="text-xs text-gray-400">{{ p.payment_date }} · {{ p.get_payment_mode_display }}{% if p.reference %} · {{ p.reference }}{% endif %}</p>
        </div>
        <span class="badge bg-green-100 text-green-700">Received</span>
      </div>
      {% empty %}
      <div class="card p-6 text-center text-gray-400 text-sm">No payments recorded yet.</div>
      {% endfor %}
    </div>
  </div>
</div>
{% endblock %}
''')

write('templates/billing/invoice_form.html', '''{% extends "base.html" %}
{% block title %}{{ title }}{% endblock %}
{% block nav_billing %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="max-w-2xl">
  <div class="flex items-center gap-3 mb-6">
    <a href="/billing/" class="text-gray-400 hover:text-gray-600">&#x2190; Billing</a>
    <h1 class="text-2xl font-bold text-gray-900">{{ title }}</h1>
  </div>
  <div class="card p-6">
    <form method="post" class="space-y-4">
      {% csrf_token %}
      {% for field in form %}
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">{{ field.label }}</label>
        {{ field }}
        {% if field.errors %}<p class="text-red-600 text-xs mt-1">{{ field.errors.0 }}</p>{% endif %}
      </div>
      {% endfor %}
      <div class="flex gap-3 pt-2">
        <button type="submit" class="btn-primary">Save Invoice</button>
        <a href="/billing/" class="btn-secondary">Cancel</a>
      </div>
    </form>
  </div>
</div>
{% endblock %}
''')

write('templates/billing/payment_form.html', '''{% extends "base.html" %}
{% block title %}Record Payment{% endblock %}
{% block nav_billing %}bg-gray-800 text-white{% endblock %}
{% block content %}
<div class="max-w-lg">
  <div class="flex items-center gap-3 mb-6">
    <a href="{% url "billing:invoice_detail" invoice.pk %}" class="text-gray-400 hover:text-gray-600">&#x2190; {{ invoice.invoice_number }}</a>
    <h1 class="text-2xl font-bold text-gray-900">Record Payment</h1>
  </div>
  <div class="card p-4 mb-6 flex items-center justify-between text-sm">
    <div>
      <p class="text-gray-400 text-xs">For Invoice</p>
      <p class="font-medium">{{ invoice.invoice_number }} – {{ invoice.client }}</p>
    </div>
    <div class="text-right">
      <p class="text-gray-400 text-xs">Amount Due</p>
      <p class="font-bold text-red-600">Rs. {{ invoice.amount|floatformat:0 }}</p>
    </div>
  </div>
  <div class="card p-6">
    <form method="post" class="space-y-4">
      {% csrf_token %}
      {% for field in form %}
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">{{ field.label }}</label>
        {{ field }}
        {% if field.errors %}<p class="text-red-600 text-xs mt-1">{{ field.errors.0 }}</p>{% endif %}
      </div>
      {% endfor %}
      <div class="flex gap-3 pt-2">
        <button type="submit" class="btn-primary">Save Payment</button>
        <a href="{% url "billing:invoice_detail" invoice.pk %}" class="btn-secondary">Cancel</a>
      </div>
    </form>
  </div>
</div>
{% endblock %}
''')

print("\n[OK] All templates written.")
