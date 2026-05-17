import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Label,
} from "recharts";
import {
  LayoutDashboard,
  Table as TableIcon,
  Activity,
  Building2,
  MapPin,
  Tag,
  Database,
  Search,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  X,
} from "lucide-react";
import {
  getHealth,
  getCityWise,
  getCategoryWise,
  getSourceWise,
  getListings,
} from "./services/api";

// ─── Color Palette ────────────────────────────────────────────────────────────
const CHART_COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#f97316",
];

const CATEGORY_COLORS: Record<string, string> = {
  Restaurant: "bg-orange-100 text-orange-700",
  Hospital: "bg-red-100 text-red-700",
  Hotel: "bg-blue-100 text-blue-700",
  School: "bg-yellow-100 text-yellow-700",
  Salon: "bg-pink-100 text-pink-700",
  Gym: "bg-green-100 text-green-700",
  Pharmacy: "bg-teal-100 text-teal-700",
  Bank: "bg-indigo-100 text-indigo-700",
  Supermarket: "bg-lime-100 text-lime-700",
  Clinic: "bg-purple-100 text-purple-700",
};

// ─── Animated Counter ─────────────────────────────────────────────────────────
function useCountUp(target: number, duration = 1200) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!target) return;
    let start = 0;
    const step = Math.ceil(target / (duration / 16));
    const timer = setInterval(() => {
      start += step;
      if (start >= target) {
        setValue(target);
        clearInterval(timer);
      } else setValue(start);
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration]);
  return value;
}

// ─── Stat Card ────────────────────────────────────────────────────────────────
function StatCard({
  icon,
  label,
  value,
  accent,
  delay = 0,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  accent: string;
  delay?: number;
}) {
  const count = useCountUp(value);
  return (
    <div
      className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-all duration-300 group"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">
            {label}
          </p>
          <p className="text-3xl font-bold text-gray-900">
            {count.toLocaleString()}
          </p>
        </div>
        <div
          className={`p-3 rounded-xl ${accent} group-hover:scale-110 transition-transform duration-200`}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────
function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-gray-100 rounded-lg ${className}`} />
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Skeleton className="h-80" />
        <Skeleton className="h-80" />
        <Skeleton className="lg:col-span-2 h-80" />
      </div>
    </div>
  );
}

// ─── Custom Tooltip ───────────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-100 shadow-lg rounded-xl px-4 py-3 text-sm">
      <p className="font-semibold text-gray-800 mb-1">
        {label || payload[0]?.name}
      </p>
      <p className="text-blue-600 font-bold">
        {payload[0]?.value?.toLocaleString()} listings
      </p>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [health, setHealth] = useState<any>(null);
  const [cityData, setCityData] = useState<any[]>([]);
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [sourceData, setSourceData] = useState<any[]>([]);
  const [listings, setListings] = useState<any[]>([]);
  const [pagination, setPagination] = useState({
    total: 0,
    total_pages: 1,
    has_next: false,
    has_prev: false,
  });
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [listingsLoading, setListingsLoading] = useState(false);

  // Filters
  const [search, setSearch] = useState("");
  const [filterCity, setFilterCity] = useState("");
  const [filterCat, setFilterCat] = useState("");

  // Static option lists populated from cityData / categoryData (available after dashboard load)
  const cities = cityData.map((c) => c.label).sort();
  const categories = categoryData.map((c) => c.label).sort();

  // Name search is client-side (API doesn't support it): filters city/cat go to API
  const filtered = listings.filter((l) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      l.business_name?.toLowerCase().includes(q) ||
      l.city?.toLowerCase().includes(q)
    );
  });

  // ── Fetch dashboard data ───────────────────────────────────────────────────
  useEffect(() => {
    const fetchAll = async () => {
      setIsLoading(true);
      try {
        const [h, city, cat, src] = await Promise.all([
          getHealth().catch(() => ({ total_listings: 0 })),
          getCityWise().catch(() => ({ data: [], total: 0 })),
          getCategoryWise().catch(() => ({ data: [], total: 0 })),
          getSourceWise().catch(() => ({ data: [], total: 0 })),
        ]);
        setHealth(h);
        setCityData(city.data || []);
        setCategoryData(
          [...(cat.data || [])].sort((a, b) => b.count - a.count).slice(0, 10),
        );
        setSourceData(src.data || []);
      } finally {
        setIsLoading(false);
      }
    };
    fetchAll();
  }, []);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [filterCity, filterCat]);

  // ── Fetch listings: re-runs on page, city filter, category filter ─────────
  useEffect(() => {
    if (activeTab !== "listings") return;
    setListingsLoading(true);
    getListings(page, 20, filterCity, filterCat)
      .then((res) => {
        setListings(res.data || []);
        setPagination({
          total: res.total ?? 0,
          total_pages: res.total_pages ?? 1,
          has_next: res.has_next ?? false,
          has_prev: res.has_prev ?? false,
        });
      })
      .catch(console.error)
      .finally(() => setListingsLoading(false));
  }, [activeTab, page, filterCity, filterCat]);

  // ── Donut center label ────────────────────────────────────────────────────
  const totalSource = sourceData.reduce((s, d) => s + d.count, 0);
  const renderCenterLabel = ({ viewBox }: any) => {
    const { cx, cy } = viewBox;
    return (
      <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central">
        <tspan x={cx} dy="-0.4em" fontSize={22} fontWeight="700" fill="#1e293b">
          {totalSource.toLocaleString()}
        </tspan>
        <tspan x={cx} dy="1.5em" fontSize={11} fill="#94a3b8" fontWeight="500">
          total
        </tspan>
      </text>
    );
  };

  return (
    <div
      className="min-h-screen flex font-sans"
      style={{ fontFamily: "'DM Sans', sans-serif", background: "#f8fafc" }}
    >
      {/* ── Sidebar ────────────────────────────────────────────────────────── */}
      <aside
        className="w-60 flex-shrink-0 flex flex-col"
        style={{ background: "#0f1629", minHeight: "100vh" }}
      >
        {/* Logo */}
        <div className="px-6 pt-8 pb-6 border-b border-white/5">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-white" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">
              BizDash
            </span>
          </div>
          <p className="text-xs text-slate-400 ml-10">Analytics Overview</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-6 space-y-1">
          {[
            {
              id: "dashboard",
              label: "Dashboard",
              icon: <LayoutDashboard className="w-4 h-4" />,
            },
            {
              id: "listings",
              label: "All Listings",
              icon: <TableIcon className="w-4 h-4" />,
            },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                activeTab === item.id
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-600/30"
                  : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        {/* DB Status */}
        <div className="px-4 pb-6">
          <div
            className="rounded-xl p-3 text-xs"
            style={{ background: "rgba(255,255,255,0.04)" }}
          >
            <div className="flex items-center gap-2 text-slate-400 mb-1">
              <Database className="w-3.5 h-3.5" />
              <span className="font-medium">Railway MySQL</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-emerald-400 font-medium">Connected</span>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main ───────────────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        {/* Top Bar */}
        <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-gray-100 px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              {activeTab === "dashboard" ? "Dashboard" : "All Listings"}
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              {activeTab === "dashboard"
                ? `${health?.total_listings?.toLocaleString() || 0} total business listings`
                : "Browse and filter all scraped listings"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1.5 rounded-full font-medium">
              Last updated: {new Date().toLocaleTimeString()}
            </span>
          </div>
        </div>

        <div className="p-8">
          {/* ── Dashboard Tab ──────────────────────────────────────────────── */}
          {activeTab === "dashboard" &&
            (isLoading ? (
              <DashboardSkeleton />
            ) : (
              <div className="space-y-6 max-w-7xl">
                {/* Stat Cards */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <StatCard
                    delay={0}
                    icon={<Activity className="w-5 h-5 text-blue-600" />}
                    label="Total Listings"
                    value={health?.total_listings || 0}
                    accent="bg-blue-50"
                  />
                  <StatCard
                    delay={100}
                    icon={<MapPin className="w-5 h-5 text-emerald-600" />}
                    label="Cities Covered"
                    value={cityData.length}
                    accent="bg-emerald-50"
                  />
                  <StatCard
                    delay={200}
                    icon={<Tag className="w-5 h-5 text-amber-600" />}
                    label="Categories"
                    value={categoryData.length}
                    accent="bg-amber-50"
                  />
                  <StatCard
                    delay={300}
                    icon={<Building2 className="w-5 h-5 text-purple-600" />}
                    label="Data Sources"
                    value={sourceData.length}
                    accent="bg-purple-50"
                  />
                </div>

                {/* Charts Row 1 */}
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                  {/* City Bar Chart: wider */}
                  <div className="lg:col-span-3 bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h3 className="font-bold text-gray-900">
                          Listings by City
                        </h3>
                        <p className="text-xs text-gray-400 mt-0.5">
                          Business count per city
                        </p>
                      </div>
                      <span className="text-xs bg-blue-50 text-blue-600 font-semibold px-3 py-1 rounded-full">
                        {cityData.length} cities
                      </span>
                    </div>
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={cityData}
                          margin={{ top: 5, right: 10, left: -20, bottom: 5 }}
                        >
                          <XAxis
                            dataKey="label"
                            tick={{ fill: "#9ca3af", fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <YAxis
                            tick={{ fill: "#9ca3af", fontSize: 11 }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <Tooltip
                            content={<CustomTooltip />}
                            cursor={{ fill: "#f1f5f9" }}
                          />
                          <Bar
                            dataKey="count"
                            radius={[6, 6, 0, 0]}
                            barSize={32}
                          >
                            {cityData.map((_, i) => (
                              <Cell
                                key={i}
                                fill={i % 2 === 0 ? "#3b82f6" : "#60a5fa"}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Source Donut: narrower */}
                  <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                    <div className="mb-6">
                      <h3 className="font-bold text-gray-900">
                        Listings by Source
                      </h3>
                      <p className="text-xs text-gray-400 mt-0.5">
                        Data origin breakdown
                      </p>
                    </div>
                    <div className="h-56">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={sourceData}
                            cx="50%"
                            cy="50%"
                            innerRadius={55}
                            outerRadius={85}
                            paddingAngle={3}
                            dataKey="count"
                            nameKey="label"
                            labelLine={false}
                            label={false}
                          >
                            {sourceData.map((_, i) => (
                              <Cell
                                key={i}
                                fill={CHART_COLORS[i % CHART_COLORS.length]}
                              />
                            ))}
                            <Label
                              content={renderCenterLabel}
                              position="center"
                            />
                          </Pie>
                          <Tooltip content={<CustomTooltip />} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    {/* Source legend with counts */}
                    <div className="space-y-2 mt-2">
                      {sourceData.map((s, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between text-sm"
                        >
                          <div className="flex items-center gap-2">
                            <div
                              className="w-2.5 h-2.5 rounded-full"
                              style={{
                                background:
                                  CHART_COLORS[i % CHART_COLORS.length],
                              }}
                            />
                            <span className="text-gray-600">{s.label}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-gray-900">
                              {s.count}
                            </span>
                            <span className="text-xs text-gray-400">
                              (
                              {totalSource
                                ? ((s.count / totalSource) * 100).toFixed(1)
                                : 0}
                              %)
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Category Horizontal Bar */}
                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="font-bold text-gray-900">
                        Top 10 Categories
                      </h3>
                      <p className="text-xs text-gray-400 mt-0.5">
                        Most common business types
                      </p>
                    </div>
                    <span className="text-xs bg-emerald-50 text-emerald-600 font-semibold px-3 py-1 rounded-full">
                      {categoryData.length} categories
                    </span>
                  </div>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={categoryData}
                        layout="vertical"
                        margin={{ top: 0, right: 40, left: 20, bottom: 0 }}
                      >
                        <XAxis
                          type="number"
                          tick={{ fill: "#9ca3af", fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          dataKey="label"
                          type="category"
                          tick={{ fill: "#4b5563", fontSize: 12 }}
                          width={100}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          content={<CustomTooltip />}
                          cursor={{ fill: "#f1f5f9" }}
                        />
                        <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={22}>
                          {categoryData.map((_, i) => (
                            <Cell
                              key={i}
                              fill={CHART_COLORS[i % CHART_COLORS.length]}
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* City breakdown table */}
                <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
                  <h3 className="font-bold text-gray-900 mb-4">
                    City Breakdown
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                    {cityData.map((c, i) => (
                      <div
                        key={i}
                        className="rounded-xl p-4 text-center"
                        style={{ background: "#f8fafc" }}
                      >
                        <p className="text-2xl font-bold text-gray-900">
                          {c.count}
                        </p>
                        <p className="text-xs text-gray-500 mt-1 font-medium">
                          {c.label}
                        </p>
                        <div className="mt-2 h-1 rounded-full bg-gray-100 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-blue-500"
                            style={{
                              width: `${(c.count / Math.max(...cityData.map((x) => x.count))) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}

          {/* ── Listings Tab ───────────────────────────────────────────────── */}
          {activeTab === "listings" && (
            <div className="max-w-7xl space-y-4">
              {/* Search + Filters */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
                <div className="flex flex-col sm:flex-row gap-3">
                  {/* Search */}
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search by name or city..."
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition"
                    />
                    {search && (
                      <button
                        onClick={() => setSearch("")}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  {/* City filter */}
                  <select
                    value={filterCity}
                    onChange={(e) => setFilterCity(e.target.value)}
                    className="text-sm border border-gray-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 bg-white text-gray-700 transition"
                  >
                    <option value="">All Cities</option>
                    {cities.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>

                  {/* Category filter */}
                  <select
                    value={filterCat}
                    onChange={(e) => setFilterCat(e.target.value)}
                    className="text-sm border border-gray-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 bg-white text-gray-700 transition"
                  >
                    <option value="">All Categories</option>
                    {categories.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>

                  {/* Clear filters */}
                  {(search || filterCity || filterCat) && (
                    <button
                      onClick={() => {
                        setSearch("");
                        setFilterCity("");
                        setFilterCat("");
                      }}
                      className="flex items-center gap-1.5 text-sm text-red-500 hover:text-red-600 font-medium px-3 py-2.5 rounded-xl hover:bg-red-50 transition"
                    >
                      <X className="w-4 h-4" /> Clear
                    </button>
                  )}
                </div>

                {/* Results count */}
                <p className="text-xs text-gray-400 mt-3">
                  Showing{" "}
                  <span className="font-semibold text-gray-700">
                    {filtered.length}
                  </span>{" "}
                  of{" "}
                  <span className="font-semibold text-gray-700">
                    {listings.length}
                  </span>{" "}
                  listings on this page
                </p>
              </div>

              {/* Table */}
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                {listingsLoading ? (
                  <div className="p-8 space-y-3">
                    {[...Array(8)].map((_, i) => (
                      <Skeleton key={i} className="h-10" />
                    ))}
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr
                          className="border-b border-gray-100"
                          style={{ background: "#f8fafc" }}
                        >
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                            #
                          </th>
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                            Business Name
                          </th>
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                            Category
                          </th>
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                            City
                          </th>
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                            Address
                          </th>
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                            Phone
                          </th>
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                            Source
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {filtered.map((item: any, i) => (
                          <tr
                            key={i}
                            className="hover:bg-blue-50/30 transition-colors duration-100 group"
                          >
                            <td className="px-6 py-4 text-gray-300 text-xs">
                              {(page - 1) * 20 + i + 1}
                            </td>
                            <td className="px-6 py-4 font-semibold text-gray-900 max-w-[180px] truncate">
                              {item.business_name}
                            </td>
                            <td className="px-6 py-4">
                              <span
                                className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${CATEGORY_COLORS[item.category] || "bg-gray-100 text-gray-700"}`}
                              >
                                {item.category}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-gray-600">
                              {item.city}
                            </td>
                            <td className="px-6 py-4 text-gray-500 max-w-[200px] truncate text-xs">
                              {item.address || "—"}
                            </td>
                            <td className="px-6 py-4 text-gray-600 font-mono text-xs">
                              {item.phone || "—"}
                            </td>
                            <td className="px-6 py-4">
                              <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 bg-slate-100 px-2 py-1 rounded-full">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                {item.source}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {filtered.length === 0 && (
                      <div className="py-16 text-center">
                        <p className="text-gray-400 font-medium">
                          No listings match your filters
                        </p>
                        <button
                          onClick={() => {
                            setSearch("");
                            setFilterCity("");
                            setFilterCat("");
                          }}
                          className="mt-2 text-sm text-blue-500 hover:underline"
                        >
                          Clear filters
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Pagination */}
                <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50/50">
                  <button
                    disabled={!pagination.has_prev}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
                  >
                    <ChevronLeft className="w-4 h-4" /> Previous
                  </button>
                  <div className="text-center">
                    <p className="text-sm font-semibold text-gray-800">
                      Page {page}{" "}
                      <span className="text-gray-400 font-normal">
                        of {pagination.total_pages}
                      </span>
                    </p>
                    <p className="text-xs text-gray-400">
                      {pagination.total.toLocaleString()} total results
                    </p>
                  </div>
                  <button
                    disabled={!pagination.has_next}
                    onClick={() => setPage((p) => p + 1)}
                    className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
                  >
                    Next <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
