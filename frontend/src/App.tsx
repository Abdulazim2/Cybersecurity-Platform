
import { useState, useEffect } from 'react'
import Login from './pages/Login'
import api from './services/api'

import {
  Activity,
  Bell,
  BrainCircuit,
  CalendarDays,
  ChevronDown,
  Database,
  Download,
  Factory,
  LayoutDashboard,
  MoreHorizontal,
  Search,
  Server,
  Settings,
  ShieldCheck,
  Users,
  Wifi,
  Clock3,
  LogOut,
} from 'lucide-react'

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const navigation = [
  { label: 'Overview', icon: LayoutDashboard },
  { label: 'Network Monitoring', icon: Activity },
  { label: 'Datasets', icon: Database },
  { label: 'AI Predictions', icon: BrainCircuit },
  { label: 'Factories', icon: Factory },
  { label: 'Users & Roles', icon: Users },
]

const datasetColors = ['#315E79', '#4F8B8D', '#A4B8B8', '#D6A75D']

type DashboardStatistics = {
  total_datasets: number
  total_records: number
  total_network_events: number
  total_predictions: number
  datasets_by_type: {
    dataset_type: string
    files_count: number
    records_count: number
  }[]
  predictions_by_label: {
    prediction_label: string
    count: number
  }[]
  factories: {
    factory_id: number
    factory_name: string
    datasets_count: number
    records_count: number
    predictions_count: number
  }[]
}


type Notification = {
  id: number
  company_id: number
  prediction_id: number | null
  title: string
  message: string
  notification_type: string
  is_read: boolean
  created_at: string
}

type NetworkEvent = {
  id: number
  company_id: number
  factory_id: number
  source_ip: string
  destination_ip: string
  protocol: string
  source_port: number | null
  destination_port: number | null
  packet_count: number | null
  bytes_transferred: number | null
  duration: number | null
  event_time: string | null
  created_at: string | null
}
type Prediction = {
  id: number
  company_id: number
  factory_id: number
  uploaded_dataset_id: number
  record_index: number | null
  model_name: string
  model_version: string | null
  prediction_label: string | null
  confidence_score: number | null
  shap_explanation: Record<string, unknown> | null
  prediction_output: Record<string, unknown> | unknown[] | null
  created_at: string
}
type FactoryItem = {
  id: number
  name: string
  location: string | null
  company_id: number
}
type CompanyItem = {
  id: number
  name: string
  industry: string | null
  email: string | null
}
type UserItem = {
  id: number
  username: string
  email: string
  company_id: number
  role_id: number
  is_active: boolean
}

type RoleItem = {
  id: number
  name: string
  description: string | null
}
type UploadedDataset = {
  dataset_id: number
  company_id: number
  factory_id: number
  uploaded_by: number
  dataset_type: string
  filename: string
  records_count: number
  created_at: string
  columns?: string[]
  records?: Record<string, unknown>[]
}
function App() {
  const [activePage, setActivePage] = useState('Overview')
  const [isGlobalSearchOpen, setIsGlobalSearchOpen] = useState(false)
  const [globalSearchQuery, setGlobalSearchQuery] = useState('')
  const [globalSearchLoading, setGlobalSearchLoading] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [checkingAuth, setCheckingAuth] = useState(true)
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
const [unreadCount, setUnreadCount] = useState(0)
const [isNotificationsOpen, setIsNotificationsOpen] = useState(false)
const [dashboardStats, setDashboardStats] = useState<DashboardStatistics | null>(null)
const [systemHealth, setSystemHealth] = useState<{
  status: string
  service: string
  database: string
  last_check: string | null
} | null>(null)

const [mlPipeline, setMlPipeline] = useState<{
  status: string
  model_loaded: boolean
  message: string
} | null>(null)

  const [selectedTimeRange, setSelectedTimeRange] = useState<'24h' | '7d' | '30d' | 'all'>('24h')
const [networkEvents, setNetworkEvents] = useState<NetworkEvent[]>([])
const [predictions, setPredictions] = useState<Prediction[]>([])
const [predictionsLoading, setPredictionsLoading] = useState(true)
const [predictionsError, setPredictionsError] = useState('')
const [selectedPrediction, setSelectedPrediction] = useState<Prediction | null>(null)
const [networkEventsLoading, setNetworkEventsLoading] = useState(true)
const [networkSearch, setNetworkSearch] = useState('')
const [protocolFilter, setProtocolFilter] = useState('All')
const [selectedNetworkEvent, setSelectedNetworkEvent] = useState<NetworkEvent | null>(null)
  const [factories, setFactories] = useState<FactoryItem[]>([])
  // Factories page state
  const [factorySearch, setFactorySearch] = useState('')
  const [factoryFormOpen, setFactoryFormOpen] = useState(false)
  const [editingFactory, setEditingFactory] = useState<FactoryItem | null>(null)
  const [factoryName, setFactoryName] = useState('')
  const [factoryLocation, setFactoryLocation] = useState('')
  const [factoryCompanyId, setFactoryCompanyId] = useState('')
  const [companies, setCompanies] = useState<CompanyItem[]>([])
  const [factoriesLoading, setFactoriesLoading] = useState(false)
  const [factorySaving, setFactorySaving] = useState(false)
  const [factoryError, setFactoryError] = useState('')
  const [factoryMessage, setFactoryMessage] = useState('')
    // Users & Roles page state
  const [users, setUsers] = useState<UserItem[]>([])
  const [roles, setRoles] = useState<RoleItem[]>([])

  const [usersLoading, setUsersLoading] = useState(false)
  const [usersSaving, setUsersSaving] = useState(false)

  const [usersError, setUsersError] = useState('')
  const [usersMessage, setUsersMessage] = useState('')

  const [userSearch, setUserSearch] = useState('')
  const [userStatusFilter, setUserStatusFilter] = useState('All')

  const [userFormOpen, setUserFormOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<UserItem | null>(null)

  const [userUsername, setUserUsername] = useState('')
  const [userEmail, setUserEmail] = useState('')
  const [userPassword, setUserPassword] = useState('')
  const [userRoleId, setUserRoleId] = useState('')
  const [userCompanyId, setUserCompanyId] = useState('')
  // Refresh factories from backend
  const loadFactories = async () => {
    setFactoriesLoading(true)
    setFactoryError('')

    try {
      const response = await api.get<FactoryItem[]>('/factories/')
      setFactories(response.data)
    } catch (error) {
      console.error('Failed to load factories:', error)
      setFactoryError('Could not load factories. Please try again.')
    } finally {
      setFactoriesLoading(false)
    }
  }

  // Open form for creating a factory
  const openFactoryForm = () => {
    setEditingFactory(null)
    setFactoryName('')
    setFactoryLocation('')
    setFactoryCompanyId('')
    setFactoryError('')
    setFactoryMessage('')
    setFactoryFormOpen(true)
  }

  // Open form for editing a factory
  const openFactoryEditForm = (factory: FactoryItem) => {
    setEditingFactory(factory)
    setFactoryName(factory.name)
    setFactoryLocation(factory.location ?? '')
    setFactoryCompanyId(String(factory.company_id))
    setFactoryError('')
    setFactoryMessage('')
    setFactoryFormOpen(true)
  }

  // Save a new factory or update an existing one
  const handleSaveFactory = async () => {
    const trimmedName = factoryName.trim()

    if (trimmedName.length < 2) {
      setFactoryError('Factory name must contain at least 2 characters.')
      return
    }

    if (
      currentUser?.role_name === 'Super Admin' &&
      !editingFactory &&
      !factoryCompanyId
    ) {
      setFactoryError('Please select a company.')
      return
    }

    setFactorySaving(true)
    setFactoryError('')
    setFactoryMessage('')

    try {
      const payload = {
        name: trimmedName,
        location: factoryLocation.trim() || null,
      }

      if (editingFactory) {
        await api.put(`/factories/${editingFactory.id}`, payload)
        setFactoryMessage('Factory updated successfully.')
      } else {
        await api.post('/factories/', {
          ...payload,
          ...(currentUser?.role_name === 'Super Admin'
            ? { company_id: Number(factoryCompanyId) }
            : {}),
        })
        setFactoryMessage('Factory created successfully.')
      }

      setFactoryFormOpen(false)
      setEditingFactory(null)
      setFactoryName('')
      setFactoryLocation('')
      setFactoryCompanyId('')

      await loadFactories()
    } catch (error: any) {
      console.error('Failed to save factory:', error)
      setFactoryError(
        error.response?.data?.detail || 'Could not save factory. Please try again.'
      )
    } finally {
      setFactorySaving(false)
    }
  }

  // Soft-delete a factory
  const handleDeleteFactory = async (factory: FactoryItem) => {
    const confirmed = window.confirm(
      `Are you sure you want to deactivate "${factory.name}"?`
    )

    if (!confirmed) return

    setFactoryError('')
    setFactoryMessage('')

    try {
      await api.delete(`/factories/${factory.id}`)
      setFactoryMessage('Factory deactivated successfully.')
      await loadFactories()
    } catch (error: any) {
      console.error('Failed to deactivate factory:', error)
      setFactoryError(
        error.response?.data?.detail ||
          'Could not deactivate factory. Please try again.'
      )
    }
  }
    // Open form for creating a new user
  const openUserForm = () => {
    setEditingUser(null)
    setUserUsername('')
    setUserEmail('')
    setUserPassword('')
    setUserRoleId('')
    setUserCompanyId('')
    setUsersError('')
    setUsersMessage('')
    setUserFormOpen(true)
  }

  // Open form for editing an existing user
  const openUserEditForm = (user: UserItem) => {
    setEditingUser(user)
    setUserUsername(user.username)
    setUserEmail(user.email)
    setUserPassword('')
    setUserRoleId(String(user.role_id))
    setUserCompanyId(String(user.company_id))
    setUsersError('')
    setUsersMessage('')
    setUserFormOpen(true)
  }

  // Save a new user or update an existing user
  const handleSaveUser = async () => {
    const username = userUsername.trim()
    const email = userEmail.trim()
    const password = userPassword.trim()

    if (username.length < 3) {
      setUsersError('Username must contain at least 3 characters.')
      return
    }

    if (!email) {
      setUsersError('Please enter an email address.')
      return
    }

    if (!userRoleId) {
      setUsersError('Please select a role.')
      return
    }

    if (!editingUser && password.length < 8) {
      setUsersError('Password must contain at least 8 characters.')
      return
    }

    if (
      currentUser?.role_name === 'Super Admin' &&
      !userCompanyId
    ) {
      setUsersError('Please select a company.')
      return
    }

    setUsersSaving(true)
    setUsersError('')
    setUsersMessage('')

    try {
      if (editingUser) {
        const payload: {
          username: string
          email: string
          role_id: number
          password?: string
        } = {
          username,
          email,
          role_id: Number(userRoleId),
        }

        if (password) {
          if (password.length < 8) {
            setUsersError('Password must contain at least 8 characters.')
            setUsersSaving(false)
            return
          }

          payload.password = password
        }

        await api.put(`/users/${editingUser.id}`, payload)

        setUsersMessage('User updated successfully.')
      } else {
        await api.post('/users/register', {
          username,
          email,
          password,
          role_id: Number(userRoleId),
          company_id:
            currentUser?.role_name === 'Super Admin'
              ? Number(userCompanyId)
              : currentUser?.company_id,
        })

        setUsersMessage('User created successfully.')
      }

      setUserFormOpen(false)
      setEditingUser(null)

      setUserUsername('')
      setUserEmail('')
      setUserPassword('')
      setUserRoleId('')
      setUserCompanyId('')

      const response = await api.get<UserItem[]>('/users/')
      setUsers(response.data)
    } catch (error: any) {
      console.error('Failed to save user:', error)

      setUsersError(
        error.response?.data?.detail ||
          'Could not save user. Please try again.'
      )
    } finally {
      setUsersSaving(false)
    }
  }

  // Deactivate a user without deleting historical records
  const handleDeactivateUser = async (user: UserItem) => {
    const confirmed = window.confirm(
      `Are you sure you want to deactivate "${user.username}"?`
    )

    if (!confirmed) return

    setUsersError('')
    setUsersMessage('')

    try {
      await api.delete(`/users/${user.id}`)

      setUsersMessage('User deactivated successfully.')

      const response = await api.get<UserItem[]>('/users/')
      setUsers(response.data)
    } catch (error: any) {
      console.error('Failed to deactivate user:', error)

      setUsersError(
        error.response?.data?.detail ||
          'Could not deactivate user. Please try again.'
      )
    }
  }
  const [uploadedDatasets, setUploadedDatasets] = useState<UploadedDataset[]>([])
  const [datasetsLoading, setDatasetsLoading] = useState(true)
  const [datasetsError, setDatasetsError] = useState('')
  const [datasetSearch, setDatasetSearch] = useState('')
  const [selectedDataset, setSelectedDataset] = useState<UploadedDataset | null>(null)
  const [datasetDetailsLoading, setDatasetDetailsLoading] = useState(false)
  const [selectedFactory, setSelectedFactory] = useState('')
  const [selectedDatasetType, setSelectedDatasetType] = useState('system_logs')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadingDataset, setUploadingDataset] = useState(false)
  const [uploadMessage, setUploadMessage] = useState('')
  const [uploadError, setUploadError] = useState('')

  const [currentUser, setCurrentUser] = useState<{
    id: number
    username: string
    email: string
    company_id: number
   role_id: number | null
   role_name: string | null
   role_description: string | null
   is_active: boolean
  } | null>(null)

  const handleOpenGlobalSearch = async () => {
    setGlobalSearchQuery('')
    setIsGlobalSearchOpen(true)
    setGlobalSearchLoading(true)

    try {
      const results = await Promise.allSettled([
        api.get<UserItem[]>('/users/'),
        api.get<Prediction[]>('/predictions/'),
      ])

      if (results[0].status === 'fulfilled') {
        setUsers(results[0].value.data)
      }

      if (results[1].status === 'fulfilled') {
        setPredictions(results[1].value.data)
      }
    } finally {
      setGlobalSearchLoading(false)
    }
  }

  useEffect(() => {
    if (!isAuthenticated) return

    const handleSearchShortcut = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        void handleOpenGlobalSearch()
      }

      if (event.key === 'Escape') {
        setIsGlobalSearchOpen(false)
      }
    }

    window.addEventListener('keydown', handleSearchShortcut)
    return () => window.removeEventListener('keydown', handleSearchShortcut)
  }, [isAuthenticated])

  const handleLoginSuccess = async () => {
    try {
      const response = await api.get('/auth/me')
      setCurrentUser(response.data)
      setIsAuthenticated(true)
    } catch {
      sessionStorage.removeItem('access_token')
      setCurrentUser(null)
      setIsAuthenticated(false)
    }
  }

  -

  // Check whether the user is already authenticated
  useEffect(() => {
    const checkAuth = async () => {
      const token = sessionStorage.getItem('access_token')

      if (!token) {
        setCheckingAuth(false)
        return
      }

      try {
        const response = await api.get('/auth/me')
        setCurrentUser(response.data)
        setIsAuthenticated(true)
      } catch {
        sessionStorage.removeItem('access_token')
        setCurrentUser(null)
        setIsAuthenticated(false)
      } finally {
        setCheckingAuth(false)
      }
    }

    checkAuth()
  }, [])

  // Load companies for Super Admin factory management
  useEffect(() => {
    if (!isAuthenticated || currentUser?.role_name !== 'Super Admin') {
      setCompanies([])
      return
    }

    const loadCompanies = async () => {
      try {
        const response = await api.get<CompanyItem[]>('/companies/')
        setCompanies(response.data)
      } catch (error) {
        console.error('Failed to load companies:', error)
        setFactoryError('Could not load companies.')
      }
    }

    loadCompanies()
  }, [isAuthenticated, currentUser?.role_name])

  // Load notifications and unread count
  useEffect(() => {
    if (!isAuthenticated) return

    const loadNotifications = async () => {
      try {
        const [notificationsResponse, countResponse] = await Promise.all([
          api.get('/notifications/'),
          api.get('/notifications/unread-count'),
        ])

        setNotifications(notificationsResponse.data)
        setUnreadCount(countResponse.data.unread_count)
      } catch (error) {
        console.error('Failed to load notifications:', error)
      }
    }

    loadNotifications()

    const interval = window.setInterval(loadNotifications, 30000)

    return () => window.clearInterval(interval)
  }, [isAuthenticated])

useEffect(() => {
  if (!isAuthenticated || activePage !== 'AI Predictions') return

  const loadPredictions = async () => {
    setPredictionsLoading(true)
    setPredictionsError('')

    try {
      const response = await api.get<Prediction[]>('/predictions/')
      setPredictions(response.data)
    } catch (error) {
      console.error('Failed to load predictions:', error)
      setPredictionsError('Failed to load AI predictions. Please try again.')
    } finally {
      setPredictionsLoading(false)
    }
  }

  loadPredictions()

  const interval = window.setInterval(loadPredictions, 30000)

  return () => window.clearInterval(interval)
}, [isAuthenticated, activePage])
// Load users and roles when Users & Roles page is opened
useEffect(() => {
  if (!isAuthenticated || activePage !== 'Users & Roles') return

  const loadUsersAndRoles = async () => {
    setUsersLoading(true)
    setUsersError('')

    try {
      const [usersResponse, rolesResponse] = await Promise.all([
        api.get<UserItem[]>('/users/'),
        api.get<RoleItem[]>('/roles/'),
      ])

      setUsers(usersResponse.data)
      setRoles(rolesResponse.data)
    } catch (error: any) {
      console.error('Failed to load users and roles:', error)

      setUsersError(
        error.response?.data?.detail ||
          'Could not load users and roles. Please try again.'
      )
    } finally {
      setUsersLoading(false)
    }
  }

  loadUsersAndRoles()

  const interval = window.setInterval(loadUsersAndRoles, 30000)

  return () => window.clearInterval(interval)
}, [isAuthenticated, activePage])
useEffect(() => {
  if (!isAuthenticated) return

  const loadDashboardStatistics = async () => {
    try {
      const hoursByRange = {
        '24h': 24,
        '7d': 168,
        '30d': 720,
        all: 0,
      }

      const response = await api.get<DashboardStatistics>(
        '/dashboard/statistics',
        {
          params: {
            hours: hoursByRange[selectedTimeRange],
          },
        }
      )
      setDashboardStats(response.data)
    } catch (error) {
      console.error('Failed to load dashboard statistics:', error)
    }
  }

  loadDashboardStatistics()

  const interval = window.setInterval(loadDashboardStatistics, 30000)

  return () => window.clearInterval(interval)
}, [isAuthenticated, selectedTimeRange])

useEffect(() => {
  if (!isAuthenticated) return

  const loadSystemHealth = async () => {
    try {
      const response = await api.get<{
        status: string
        service: string
        database: string
        last_check: string
      }>('/health')

      setSystemHealth(response.data)
    } catch (error) {
      console.error('Failed to load system health:', error)

      setSystemHealth({
        status: 'Unavailable',
        service: 'Backend API',
        database: 'Unknown',
        last_check: null,
      })
    }
  }

  loadSystemHealth()

  const interval = window.setInterval(loadSystemHealth, 30000)

  return () => window.clearInterval(interval)
}, [isAuthenticated])

useEffect(() => {
  if (!isAuthenticated) return

  const loadMlPipeline = async () => {
    try {
      const response = await api.get<{
        status: string
        model_loaded: boolean
        message: string
      }>('/ml/status')

      setMlPipeline(response.data)
    } catch (error) {
      console.error('Failed to load ML pipeline status:', error)

      setMlPipeline({
        status: 'Unavailable',
        model_loaded: false,
        message: 'ML status unavailable',
      })
    }
  }

  loadMlPipeline()

  const interval = window.setInterval(loadMlPipeline, 30000)

  return () => window.clearInterval(interval)
}, [isAuthenticated])


useEffect(() => {
  if (!isAuthenticated) return

  const loadNetworkEvents = async () => {
    try {
      const response = await api.get<NetworkEvent[]>('/network-events/')
      setNetworkEvents(response.data)
    } catch (error) {
      console.error('Failed to load network events:', error)
    } finally {
      setNetworkEventsLoading(false)
    }
  }

  loadNetworkEvents()

  const interval = window.setInterval(loadNetworkEvents, 30000)

  return () => window.clearInterval(interval)
}, [isAuthenticated])

useEffect(() => {
  if (!isAuthenticated) return

  const loadDatasetData = async () => {
    setDatasetsLoading(true)
    setDatasetsError('')

    try {
      const [factoriesResponse, datasetsResponse] = await Promise.all([
        api.get<FactoryItem[]>('/factories/'),
        api.get<UploadedDataset[]>('/data-upload/'),
      ])

      setFactories(factoriesResponse.data)
      setUploadedDatasets(datasetsResponse.data)
    } catch (error) {
      console.error('Failed to load dataset data:', error)
      setDatasetsError('Could not load factories or uploaded datasets.')
    } finally {
      setDatasetsLoading(false)
    }
  }

  loadDatasetData()
}, [isAuthenticated])
const handleMarkAsRead = async (notificationId: number) => {
  try {
    await api.patch(`/notifications/${notificationId}/read`)

    setNotifications((previous) =>
      previous.map((notification) =>
        notification.id === notificationId
          ? { ...notification, is_read: true }
          : notification
      )
    )

    const response = await api.get('/notifications/unread-count')
    setUnreadCount(response.data.unread_count)
  } catch (error) {
    console.error('Failed to mark notification as read:', error)
  }
}
  const handleExportReport = () => {
    const rows: unknown[][] = [
      ['Section', 'Metric', 'Value'],
      ['Dashboard', 'Total Datasets', dashboardStats?.total_datasets ?? 0],
      ['Dashboard', 'Total Records', dashboardStats?.total_records ?? 0],
      ['Dashboard', 'Network Events', dashboardStats?.total_network_events ?? 0],
      ['Dashboard', 'AI Predictions', dashboardStats?.total_predictions ?? 0],
      [],
      [
        'Network Events',
        'ID',
        'Factory ID',
        'Protocol',
        'Source IP',
        'Destination IP',
        'Event Time',
        'Created At',
        'Packets',
        'Bytes Transferred'
      ],
      ...networkEvents.map((event) => [
        'Network Event',
        event.id,
        event.factory_id,
        event.protocol,
        event.source_ip,
        event.destination_ip,
        event.event_time ?? '',
        event.created_at ?? '',
        event.packet_count ?? '',
        event.bytes_transferred ?? ''
      ])
    ]

    const csvCell = (value: unknown) =>
      `"${String(value ?? '').replace(/"/g, '""')}"`

    const csvContent =
      '\uFEFF' +
      rows.map((row) => row.map(csvCell).join(',')).join('\r\n')

    const blob = new Blob([csvContent], {
      type: 'text/csv;charset=utf-8;'
    })

    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')

    link.href = url
    link.download = `cybersecurity-dashboard-report-${new Date().toISOString().slice(0, 10)}.csv`

    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }
  const stats = [
    {
      label: 'Total Datasets',
      value: dashboardStats ? String(dashboardStats.total_datasets) : 'â€”',
      change: 'Files uploaded',
      icon: Database,
    },
    {
      label: 'Total Records',
      value: dashboardStats ? String(dashboardStats.total_records) : 'â€”',
      change: 'Across all datasets',
      icon: Server,
    },
    {
      label: 'Network Events',
      value: dashboardStats ? String(dashboardStats.total_network_events) : 'â€”',
      change: 'Events recorded',
      icon: Wifi,
    },
    {
      label: 'AI Predictions',
      value: dashboardStats ? String(dashboardStats.total_predictions) : 'â€”',
      change: 'Predictions recorded',
      icon: BrainCircuit,
    },
  ]

  const datasetTypeLabels: Record<string, string> = {
    traffic_logs: 'Traffic Logs',
    system_logs: 'System Logs',
    iot_logs: 'IoT Behaviour',
    authorization_logs: 'Authorization',
  }

  const datasetData = (dashboardStats?.datasets_by_type ?? []).map((item) => ({
    name: datasetTypeLabels[item.dataset_type] || item.dataset_type,
    value: item.records_count,
  }))

  // Build chart data from real network events.
  // Use event_time first and created_at as a fallback.
  const chartNow = new Date()
  const chartHours = {
    '24h': 24,
    '7d': 168,
    '30d': 720,
    all: 0,
  }[selectedTimeRange]

  const chartStart = chartHours === 0
    ? null
    : new Date(chartNow.getTime() - chartHours * 60 * 60 * 1000)

  const chartBuckets = new Map<string, number>()

  networkEvents.forEach((event) => {
    const timestamp = event.event_time || event.created_at
    if (!timestamp) return

    const eventDate = new Date(timestamp)

    if (Number.isNaN(eventDate.getTime())) return
    if (chartStart && eventDate < chartStart) return
    if (eventDate > chartNow) return

    const bucketDate = new Date(eventDate)

    if (selectedTimeRange === '24h') {
      bucketDate.setMinutes(0, 0, 0)
    } else {
      bucketDate.setHours(0, 0, 0, 0)
    }

    const key = bucketDate.toISOString()

    chartBuckets.set(key, (chartBuckets.get(key) ?? 0) + 1)
  })

  const trafficChartData = Array.from(chartBuckets.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, events]) => {
      const date = new Date(key)

      return {
        time: selectedTimeRange === '24h'
          ? date.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })
          : date.toLocaleDateString([], {
              month: 'short',
              day: 'numeric',
            }),
        events,
      }
    })


  const filteredNetworkEvents = networkEvents.filter((event) => {
    const searchTerm = networkSearch.trim().toLowerCase()

    const matchesSearch =
      !searchTerm ||
      event.source_ip.toLowerCase().includes(searchTerm) ||
      event.destination_ip.toLowerCase().includes(searchTerm) ||
      event.protocol.toLowerCase().includes(searchTerm)

    const matchesProtocol =
      protocolFilter === 'All' ||
      event.protocol.toUpperCase() === protocolFilter

    return matchesSearch && matchesProtocol
  })

  const searchTerm = globalSearchQuery.trim().toLowerCase()

  const globalSearchResults = searchTerm
    ? [
        ...users
          .filter((item) =>
            `${item.username} ${item.email}`.toLowerCase().includes(searchTerm)
          )
          .map((item) => ({
            id: `user-${item.id}`,
            category: 'User',
            title: item.username,
            subtitle: item.email,
            page: 'Users & Roles',
          })),

        ...factories
          .filter((item) =>
            `${item.name} ${item.location || ''}`.toLowerCase().includes(searchTerm)
          )
          .map((item) => ({
            id: `factory-${item.id}`,
            category: 'Factory',
            title: item.name,
            subtitle: item.location || `Company #${item.company_id}`,
            page: 'Factories',
          })),

        ...uploadedDatasets
          .filter((item) =>
            `${item.filename} ${item.dataset_type}`.toLowerCase().includes(searchTerm)
          )
          .map((item) => ({
            id: `dataset-${item.dataset_id}`,
            category: 'Dataset',
            title: item.filename,
            subtitle: `${item.dataset_type} ? ${item.records_count} records`,
            page: 'Datasets',
          })),

        ...networkEvents
          .filter((item) =>
            `${item.source_ip} ${item.destination_ip} ${item.protocol}`
              .toLowerCase()
              .includes(searchTerm)
          )
          .map((item) => ({
            id: `event-${item.id}`,
            category: 'Network Event',
            title: `${item.source_ip} ? ${item.destination_ip}`,
            subtitle: `${item.protocol} ? Event #${item.id}`,
            page: 'Network Monitoring',
          })),

        ...predictions
          .filter((item) =>
            `${item.model_name} ${item.prediction_label || ''}`
              .toLowerCase()
              .includes(searchTerm)
          )
          .map((item) => ({
            id: `prediction-${item.id}`,
            category: 'AI Prediction',
            title: item.model_name,
            subtitle: `${item.prediction_label || 'Unlabeled'} ? Dataset #${item.uploaded_dataset_id}`,
            page: 'AI Predictions',
          })),
      ].slice(0, 15)
    : []

  if (checkingAuth) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F4F6F8]">
        <p className="text-sm text-[#667482]">
          Checking authentication...
        </p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  return (
    <div className="min-h-screen bg-[#F4F6F8] text-[#202B36]">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-[250px] flex-col border-r border-[#E5E9ED] bg-white lg:flex">

        <div className="flex h-[76px] items-center gap-3 border-b border-[#E9EDF0] px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#203D50] text-white">
            <ShieldCheck size={23} />
          </div>

          <div>
            <h1 className="text-sm font-bold tracking-wide">
              INDUSTRIAL
            </h1>
            <p className="text-[11px] tracking-[2px] text-[#75818D]">
              SECURITY PLATFORM
            </p>
          </div>
        </div>

        <div className="px-4 pt-7">
          <p className="mb-3 px-3 text-[10px] font-semibold tracking-[1.5px] text-[#98A2AC]">
            WORKSPACE
          </p>

          <nav className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon
              const active = activePage === item.label

              return (
                <button
                  key={item.label}
                  onClick={() => setActivePage(item.label)}
                  className={`flex w-full items-center gap-3 rounded-md px-3 py-3 text-left text-[13px] transition ${
                    active
                      ? 'bg-[#EAF0F4] font-semibold text-[#24485F]'
                      : 'text-[#667482] hover:bg-[#F4F6F8]'
                  }`}
                >
                  <Icon size={18} />
                  {item.label}
                </button>
              )
            })}
          </nav>
        </div>

        <div className="mt-auto border-t border-[#E9EDF0] p-5">

          <button
            type="button"
            onClick={() => setActivePage('Settings')}
            className={`flex w-full items-center gap-3 rounded-md px-2 py-2 text-sm transition ${
              activePage === 'Settings'
                ? 'bg-[#EAF0F4] font-semibold text-[#24485F]'
                : 'text-[#667482] hover:bg-[#F4F6F8]'
            }`}
          >
            <Settings size={18} />
            Settings
          </button>

          <div className="relative mt-5">

  <button
    type="button"
    onClick={() => setIsAccountMenuOpen(!isAccountMenuOpen)}
    className="flex w-full items-center gap-3 rounded-md px-2 py-2 text-left transition hover:bg-[#F4F6F8]"
  >
    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#E8EEF2] text-sm font-semibold text-[#315E79]">
      {(currentUser?.username || 'User').slice(0, 2).toUpperCase()}
    </div>

    <div className="min-w-0 flex-1">
      <p className="truncate text-xs font-semibold">
        {currentUser?.username || 'User'}
      </p>

      <p className="truncate text-[11px] text-[#8A959F]">
        {currentUser?.email || 'Account'}
      </p>

      <p className="truncate text-[11px] font-medium text-[#315E79]">
        {currentUser?.role_name || 'No Role'}
      </p>
    </div>

    <ChevronDown
      size={15}
      className={`shrink-0 text-[#89939D] transition-transform ${
        isAccountMenuOpen ? 'rotate-180' : ''
      }`}
    />
  </button>

  {isAccountMenuOpen && (
    <div className="absolute bottom-full left-0 z-50 mb-2 w-full rounded-lg border border-[#E1E6EA] bg-white p-3 shadow-lg">

      <p className="text-xs font-semibold text-[#263746]">
        Account Details
      </p>

      <div className="mt-3 space-y-2 text-xs">
        <div>
          <p className="text-[#89939D]">Username</p>
          <p className="font-medium text-[#263746]">
            {currentUser?.username}
          </p>
        </div>

        <div>
          <p className="text-[#89939D]">Email</p>
          <p className="break-all font-medium text-[#263746]">
            {currentUser?.email}
          </p>
        </div>

        <div>
          <p className="text-[#89939D]">Role</p>
          <p className="font-medium text-[#315E79]">
            {currentUser?.role_name || 'No Role'}
          </p>
        </div>
      </div>

      <button
        type="button"
        onClick={() => {
          setActivePage('My Profile')
          setIsAccountMenuOpen(false)
        }}
        className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm text-[#52616D] transition hover:bg-[#F4F6F8]"
      >
        My Profile
      </button>
      <button
        type="button"
        onClick={() => {
          sessionStorage.removeItem('access_token')
          setCurrentUser(null)
          setIsAuthenticated(false)
          setIsAccountMenuOpen(false)
          setActivePage('Overview')
        }}
        className="mt-4 flex w-full items-center gap-2 border-t border-[#E9EDF0] pt-3 text-sm text-red-600 transition hover:text-red-700"
      >
        <LogOut size={16} />
        Sign Out
      </button>

    </div>
  )}

</div>

        </div>
      </aside>

      <main className="min-h-screen lg:ml-[250px]">

        <header className="flex h-[76px] items-center justify-between border-b border-[#E5E9ED] bg-white px-5 sm:px-8">
          <div>
            <p className="text-[11px] text-[#89939D]">
              Workspace / {activePage}
            </p>

            <h2 className="mt-1 text-lg font-semibold">
              {activePage}
            </h2>
          </div>

          <div className="flex items-center gap-3">

            <button
              type="button"
              onClick={() => void handleOpenGlobalSearch()}
              className="hidden items-center gap-2 rounded-md border border-[#E5E9ED] px-3 py-2 text-xs text-[#89939D] transition hover:border-[#AAB8C2] hover:bg-[#F8FAFB] md:flex"
              title="Search anything (Ctrl + K)"
            >
              <Search size={15} />
              <span>Search anything...</span>
              <span className="ml-5 rounded border border-[#E5E9ED] px-1.5 py-0.5">
                Ctrl K
              </span>
            </button>

            <div className="relative">
  <button
    onClick={() => setIsNotificationsOpen((previous) => !previous)}
    className="relative rounded-md border border-[#E5E9ED] p-2 text-[#687684] transition hover:bg-[#F4F6F8]"
    title="Notifications"
  >
    <Bell size={18} />

    {unreadCount > 0 && (
      <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-[#C56B56] px-1 text-[10px] font-bold text-white">
        {unreadCount > 99 ? '99+' : unreadCount}
      </span>
    )}
  </button>

  {isNotificationsOpen && (
    <div className="absolute right-0 top-12 z-50 w-[340px] overflow-hidden rounded-lg border border-[#E5E9ED] bg-white shadow-xl sm:w-[400px]">
      <div className="flex items-center justify-between border-b border-[#E5E9ED] px-4 py-3">
        <div>
          <h3 className="text-sm font-semibold text-[#263746]">
            Notifications
          </h3>
          <p className="mt-0.5 text-xs text-[#89939D]">
            {unreadCount} unread notifications
          </p>
        </div>

        <button
          onClick={() => setIsNotificationsOpen(false)}
          className="rounded-md p-1 text-[#89939D] hover:bg-[#F4F6F8]"
        >
          <span className="text-lg">Ã—</span>
        </button>
      </div>

      <div className="max-h-[400px] overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="px-4 py-10 text-center">
            <Bell className="mx-auto mb-2 text-[#AAB4BD]" size={25} />
            <p className="text-sm text-[#687684]">
              No notifications yet
            </p>
          </div>
        ) : (
          notifications.map((notification) => (
            <button
              key={notification.id}
              onClick={() => {
                if (!notification.is_read) {
                  handleMarkAsRead(notification.id)
                }
              }}
              className={`block w-full border-b border-[#EEF1F3] px-4 py-3 text-left transition hover:bg-[#F8FAFB] ${
                !notification.is_read ? 'bg-[#F4F8FA]' : 'bg-white'
              }`}
            >
              <div className="flex items-start gap-3">
                <span
                  className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                    !notification.is_read
                      ? 'bg-[#C56B56]'
                      : 'bg-[#C9D1D8]'
                  }`}
                />

                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-[#263746]">
                      {notification.title}
                    </p>

                    <span
                      className={`shrink-0 rounded px-2 py-0.5 text-[10px] font-semibold ${
                        notification.notification_type === 'critical'
                          ? 'bg-red-50 text-red-600'
                          : notification.notification_type === 'warning'
                            ? 'bg-amber-50 text-amber-600'
                            : 'bg-blue-50 text-blue-600'
                      }`}
                    >
                      {notification.notification_type}
                    </span>
                  </div>

                  <p className="mt-1 text-xs leading-5 text-[#687684]">
                    {notification.message}
                  </p>

                  <p className="mt-2 text-[10px] text-[#9AA4AD]">
                    {new Date(notification.created_at).toLocaleString()}
                    {!notification.is_read && (
                      <span className="ml-2 font-semibold text-[#398C70]">
                        â€¢ Click to mark as read
                      </span>
                    )}
                  </p>
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  )}
</div>

            <div className="hidden items-center gap-2 rounded-md bg-[#F4F6F8] px-3 py-2 sm:flex">
              <span className="h-2 w-2 rounded-full bg-[#398C70]" />
              <span className="text-xs font-medium text-[#52616D]">
                System Online
              </span>
            </div>

          </div>
        </header>

        <div className="mx-auto max-w-[1500px] p-5 sm:p-8">

          {activePage === 'Settings' ? (
            <section className="mx-auto max-w-4xl space-y-6">
              <div>
                <p className="text-xs font-medium text-[#82909C]">PREFERENCES</p>
                <h1 className="mt-2 text-2xl font-semibold text-[#263746]">Settings</h1>
                <p className="mt-1 text-sm text-[#82909C]">
                  Manage your platform preferences.
                </p>
              </div>

              <div className="rounded-lg border border-[#E5E9ED] bg-white p-6">
                <h2 className="text-base font-semibold text-[#263746]">Appearance</h2>
                <p className="mt-1 text-sm text-[#82909C]">
                  Choose how the platform should look.
                </p>

                <select
                  className="mt-4 w-full max-w-xs rounded-md border border-[#DCE2E7] bg-white px-3 py-2 text-sm text-[#263746]"
                  defaultValue={localStorage.getItem('platform_theme') || 'light'}
                  onChange={(e) => {
                    localStorage.setItem('platform_theme', e.target.value)
                    document.documentElement.classList.toggle('dark', e.target.value === 'dark')
                  }}
                >
                  <option value="light">Light Mode</option>
                  <option value="dark">Dark Mode</option>
                </select>
              </div>

              <div className="rounded-lg border border-[#E5E9ED] bg-white p-6">
                <h2 className="text-base font-semibold text-[#263746]">Notifications</h2>
                <p className="mt-1 text-sm text-[#82909C]">
                  Enable or disable platform notification preferences.
                </p>

                <label className="mt-5 flex items-center justify-between gap-4">
                  <span className="text-sm font-medium text-[#52616D]">
                    Enable Notifications
                  </span>
                  <input
                    type="checkbox"
                    defaultChecked={localStorage.getItem('platform_notifications') !== 'false'}
                    onChange={(e) => {
                      localStorage.setItem('platform_notifications', String(e.target.checked))
                    }}
                    className="h-4 w-4 accent-[#315E79]"
                  />
                </label>
              </div>

              <button
                type="button"
                onClick={() => setActivePage('Overview')}
                className="rounded-md bg-[#24485F] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#19394E]"
              >
                Back to Overview
              </button>
            </section>
          ) : activePage === 'My Profile' ? (
            <section className="space-y-6">

              <div className="rounded-lg border border-[#E5E9ED] bg-white p-6">
                <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
                  <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[#E8EEF2] text-2xl font-semibold text-[#315E79]">
                    {(currentUser?.username || 'User').slice(0, 2).toUpperCase()}
                  </div>

                  <div className="flex-1">
                    <h1 className="text-xl font-semibold text-[#263746]">
                      {currentUser?.username || 'User'}
                    </h1>

                    <p className="mt-1 text-sm text-[#82909C]">
                      {currentUser?.email || 'No email available'}
                    </p>

                    <span className="mt-3 inline-flex rounded-md bg-[#EAF0F4] px-3 py-1 text-xs font-semibold text-[#315E79]">
                      {currentUser?.role_name || 'No Role'}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => setActivePage('Overview')}
                    className="rounded-md bg-[#24485F] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#19394E]"
                  >
                    Back to Overview
                  </button>
                </div>
              </div>

              <div>
                <h2 className="mb-4 text-sm font-semibold text-[#263746]">
                  Personal Information
                </h2>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">

                  <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                    <p className="text-xs text-[#89949E]">Username</p>
                    <p className="mt-2 text-sm font-semibold text-[#263746]">
                      {currentUser?.username || 'Not available'}
                    </p>
                  </div>

                  <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                    <p className="text-xs text-[#89949E]">Email Address</p>
                    <p className="mt-2 break-all text-sm font-semibold text-[#263746]">
                      {currentUser?.email || 'Not available'}
                    </p>
                  </div>

                  <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                    <p className="text-xs text-[#89949E]">Company ID</p>
                    <p className="mt-2 text-sm font-semibold text-[#263746]">
                      {currentUser?.company_id ?? 'Not available'}
                    </p>
                  </div>

                  <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                    <p className="text-xs text-[#89949E]">Account Status</p>
                    <p className={`mt-2 text-sm font-semibold ${
                      currentUser?.is_active
                        ? 'text-[#438264]'
                        : 'text-red-600'
                    }`}>
                      {currentUser?.is_active ? 'Active' : 'Inactive'}
                    </p>
                  </div>

                  <div className="rounded-lg border border-[#E5E9ED] bg-white p-5 md:col-span-2">
                    <p className="text-xs text-[#89949E]">Role</p>
                    <p className="mt-2 text-sm font-semibold text-[#315E79]">
                      {currentUser?.role_name || 'No Role'}
                    </p>

                    <p className="mt-2 text-sm text-[#82909C]">
                      {currentUser?.role_description || 'No role description available'}
                    </p>
                  </div>

                </div>
              </div>

            </section>
          ) : activePage === 'Network Monitoring' ? (
            <section className="space-y-6">

              <div>
                <p className="text-xs font-medium text-[#82909C]">
                  NETWORK SECURITY
                </p>
                <h1 className="mt-2 text-2xl font-semibold text-[#263746]">
                  Network Monitoring
                </h1>
                <p className="mt-1 text-sm text-[#82909C]">
                  Monitor and inspect recorded network traffic events.
                </p>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">

                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <p className="text-xs font-medium text-[#82909C]">
                    Total Events
                  </p>
                  <p className="mt-2 text-2xl font-semibold text-[#263746]">
                    {networkEvents.length}
                  </p>
                  <p className="mt-1 text-xs text-[#89949E]">
                    Recorded network events
                  </p>
                </div>

                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <p className="text-xs font-medium text-[#82909C]">
                    TCP Events
                  </p>
                  <p className="mt-2 text-2xl font-semibold text-[#315E79]">
                    {networkEvents.filter((event) => event.protocol.toUpperCase() === 'TCP').length}
                  </p>
                  <p className="mt-1 text-xs text-[#89949E]">
                    TCP protocol traffic
                  </p>
                </div>

                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <p className="text-xs font-medium text-[#82909C]">
                    UDP Events
                  </p>
                  <p className="mt-2 text-2xl font-semibold text-[#438264]">
                    {networkEvents.filter((event) => event.protocol.toUpperCase() === 'UDP').length}
                  </p>
                  <p className="mt-1 text-xs text-[#89949E]">
                    UDP protocol traffic
                  </p>
                </div>

              </div>

              <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">

                <div className="mb-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                  <div>
                    <h2 className="text-base font-semibold text-[#263746]">
                      Network Events
                    </h2>
                    <p className="mt-1 text-xs text-[#89949E]">
                      Search, filter and inspect recorded events.
                    </p>
                  </div>

                  <span className="text-xs text-[#82909C]">
                    Showing {filteredNetworkEvents.length} of {networkEvents.length} events
                  </span>
                </div>

                <div className="mb-5 flex flex-col gap-3 sm:flex-row">

                  <div className="flex flex-1 items-center gap-2 rounded-md border border-[#DCE2E7] px-3 py-2.5">
                    <Search size={16} className="text-[#89949E]" />
                    <input
                      type="text"
                      value={networkSearch}
                      onChange={(e) => setNetworkSearch(e.target.value)}
                      placeholder="Search source or destination IP..."
                      className="w-full bg-transparent text-sm text-[#263746] outline-none placeholder:text-[#A0AAB3]"
                    />
                  </div>

                  <select
                    value={protocolFilter}
                    onChange={(e) => setProtocolFilter(e.target.value)}
                    className="rounded-md border border-[#DCE2E7] bg-white px-3 py-2.5 text-sm text-[#52616D] outline-none"
                  >
                    <option value="All">All Protocols</option>
                    <option value="TCP">TCP</option>
                    <option value="UDP">UDP</option>
                  </select>

                </div>

                {selectedNetworkEvent && (
                  <div className="mb-5 rounded-lg border border-[#DCE2E7] bg-[#F8FAFB] p-5">

                    <div className="mb-4 flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-semibold text-[#263746]">
                          Event Details
                        </h3>
                        <p className="mt-1 text-xs text-[#82909C]">
                          Event ID: {selectedNetworkEvent.id}
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={() => setSelectedNetworkEvent(null)}
                        className="rounded-md border border-[#DCE2E7] bg-white px-3 py-1.5 text-xs text-[#52616D] hover:bg-[#F0F3F5]"
                      >
                        Close
                      </button>
                    </div>

                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">

                      <div>
                        <p className="text-xs text-[#89949E]">Protocol</p>
                        <p className="mt-1 text-sm font-semibold text-[#263746]">
                          {selectedNetworkEvent.protocol}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-[#89949E]">Source IP</p>
                        <p className="mt-1 text-sm font-semibold text-[#263746]">
                          {selectedNetworkEvent.source_ip}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-[#89949E]">Destination IP</p>
                        <p className="mt-1 text-sm font-semibold text-[#263746]">
                          {selectedNetworkEvent.destination_ip}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-[#89949E]">Source Port</p>
                        <p className="mt-1 text-sm font-semibold text-[#263746]">
                          {selectedNetworkEvent.source_port ?? 'â€”'}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-[#89949E]">Destination Port</p>
                        <p className="mt-1 text-sm font-semibold text-[#263746]">
                          {selectedNetworkEvent.destination_port ?? 'â€”'}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-[#89949E]">Packet Count</p>
                        <p className="mt-1 text-sm font-semibold text-[#263746]">
                          {selectedNetworkEvent.packet_count?.toLocaleString() ?? 'â€”'}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-[#89949E]">Bytes Transferred</p>
                        <p className="mt-1 text-sm font-semibold text-[#263746]">
                          {selectedNetworkEvent.bytes_transferred?.toLocaleString() ?? 'â€”'}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-[#89949E]">Duration</p>
                        <p className="mt-1 text-sm font-semibold text-[#263746]">
                          {selectedNetworkEvent.duration != null
                            ? `${selectedNetworkEvent.duration} seconds`
                            : 'â€”'}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs text-[#89949E]">Factory ID</p>
                        <p className="mt-1 text-sm font-semibold text-[#263746]">
                          {selectedNetworkEvent.factory_id}
                        </p>
                      </div>

                      <div className="sm:col-span-2 lg:col-span-3">
                        <p className="text-xs text-[#89949E]">Event Time</p>
                        <p className="mt-1 text-sm font-semibold text-[#263746]">
                          {(selectedNetworkEvent.event_time || selectedNetworkEvent.created_at)
                            ? new Date(selectedNetworkEvent.event_time || selectedNetworkEvent.created_at!).toLocaleString()
                            : 'â€”'}
                        </p>
                      </div>

                    </div>
                  </div>
                )}

                <div className="overflow-x-auto">
                  <table className="w-full min-w-[850px] text-left text-xs">

                    <thead>
                      <tr className="border-b border-[#E9EDF0] text-[10px] font-semibold tracking-wide text-[#89949E]">
                        <th className="pb-3 pr-4">PROTOCOL</th>
                        <th className="pb-3 pr-4">SOURCE IP</th>
                        <th className="pb-3 pr-4">DESTINATION IP</th>
                        <th className="pb-3 pr-4">PACKETS</th>
                        <th className="pb-3 pr-4">BYTES</th>
                        <th className="pb-3 pr-4">EVENT TIME</th>
                        <th className="pb-3">ACTION</th>
                      </tr>
                    </thead>

                    <tbody>
                      {networkEventsLoading ? (
                        <tr>
                          <td colSpan={7} className="py-10 text-center text-[#89949E]">
                            Loading network events...
                          </td>
                        </tr>
                      ) : filteredNetworkEvents.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-10 text-center text-[#89949E]">
                            {networkEvents.length === 0
                              ? 'No network events have been recorded yet.'
                              : 'No events match your search or filter.'}
                          </td>
                        </tr>
                      ) : (
                        filteredNetworkEvents.map((event) => {
                          const eventDate = event.event_time || event.created_at

                          return (
                            <tr key={event.id} className="border-b border-[#F0F2F4] last:border-0">
                              <td className="py-4 pr-4">
                                <span className={`rounded px-2 py-1 text-[10px] font-semibold ${
                                  event.protocol.toUpperCase() === 'TCP'
                                    ? 'bg-[#EAF0F4] text-[#315E79]'
                                    : event.protocol.toUpperCase() === 'UDP'
                                      ? 'bg-[#EAF5EF] text-[#438264]'
                                      : 'bg-[#F1F3F5] text-[#667482]'
                                }`}>
                                  {event.protocol}
                                </span>
                              </td>

                              <td className="py-4 pr-4 font-medium text-[#52616D]">
                                {event.source_ip}
                                <span className="block mt-1 text-[10px] text-[#A0AAB3]">
                                  Port: {event.source_port ?? 'â€”'}
                                </span>
                              </td>

                              <td className="py-4 pr-4 font-medium text-[#52616D]">
                                {event.destination_ip}
                                <span className="block mt-1 text-[10px] text-[#A0AAB3]">
                                  Port: {event.destination_port ?? 'â€”'}
                                </span>
                              </td>

                              <td className="py-4 pr-4 text-[#778590]">
                                {event.packet_count?.toLocaleString() ?? 'â€”'}
                              </td>

                              <td className="py-4 pr-4 text-[#778590]">
                                {event.bytes_transferred?.toLocaleString() ?? 'â€”'}
                              </td>

                              <td className="py-4 pr-4 text-[#778590]">
                                {eventDate ? new Date(eventDate).toLocaleString() : 'â€”'}
                              </td>

                              <td className="py-4">
                                <button
                                  type="button"
                                  onClick={() => setSelectedNetworkEvent(event)}
                                  className="rounded-md border border-[#DCE2E7] px-3 py-1.5 text-xs font-medium text-[#315E79] transition hover:bg-[#EAF0F4]"
                                >
                                  Details
                                </button>
                              </td>
                            </tr>
                          )
                        })
                      )}
                    </tbody>

                  </table>
                </div>

              </div>

            </section>
          ) : activePage === 'Datasets' ? (
            <section className="space-y-6">

              <div>
                <h1 className="text-2xl font-semibold text-[#263746]">Datasets</h1>
                <p className="mt-1 text-sm text-[#82909C]">
                  Upload, manage, and inspect industrial security datasets.
                </p>
              </div>

              <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                <h2 className="mb-1 text-base font-semibold text-[#263746]">
                  Upload New Dataset
                </h2>
                <p className="mb-5 text-xs text-[#82909C]">
                  Supported formats: CSV and JSON. Maximum file size: 10 MB.
                </p>

                <form
                  onSubmit={async (event) => {
                    event.preventDefault()
                    setUploadMessage('')
                    setUploadError('')

                    if (!selectedFactory || !selectedFile) {
                      setUploadError('Please select a factory and a file.')
                      return
                    }

                    const formData = new FormData()
                    formData.append('factory_id', selectedFactory)
                    formData.append('dataset_type', selectedDatasetType)
                    formData.append('file', selectedFile)

                    setUploadingDataset(true)

                    try {
                      await api.post('/data-upload/', formData)

                      setUploadMessage('Dataset uploaded successfully!')
                      setSelectedFile(null)

                      const response = await api.get<UploadedDataset[]>('/data-upload/')
                      setUploadedDatasets(response.data)
                    } catch (error) {
                      const message = (
                        error as { response?: { data?: { detail?: string } } }
                      ).response?.data?.detail

                      setUploadError(message || 'Dataset upload failed.')
                    } finally {
                      setUploadingDataset(false)
                    }
                  }}
                  className="grid grid-cols-1 gap-4 md:grid-cols-2"
                >

                  <div>
                    <label className="mb-2 block text-xs font-semibold text-[#53616E]">
                      Factory
                    </label>
                    <select
                      value={selectedFactory}
                      onChange={(event) => setSelectedFactory(event.target.value)}
                      required
                      className="w-full rounded-md border border-[#DCE2E7] bg-white px-3 py-2.5 text-sm outline-none focus:border-[#315E79]"
                    >
                      <option value="">Select a factory</option>
                      {factories.map((factory) => (
                        <option key={factory.id} value={factory.id}>
                          {factory.name}
                        </option>
                      ))}
                    </select>
                    {factories.length === 0 && (
                      <p className="mt-2 text-xs text-[#A06B35]">
                        No factories available for your company.
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="mb-2 block text-xs font-semibold text-[#53616E]">
                      Dataset Type
                    </label>
                    <select
                      value={selectedDatasetType}
                      onChange={(event) => setSelectedDatasetType(event.target.value)}
                      className="w-full rounded-md border border-[#DCE2E7] bg-white px-3 py-2.5 text-sm outline-none focus:border-[#315E79]"
                    >
                      <option value="system_logs">System Logs</option>
                      <option value="traffic_logs">Traffic Logs</option>
                      <option value="iot_logs">IoT Behaviour Logs</option>
                      <option value="authorization_logs">Authorization Logs</option>
                    </select>
                  </div>

                  <div className="md:col-span-2">
                    <label className="mb-2 block text-xs font-semibold text-[#53616E]">
                      Dataset File
                    </label>
                    <input
                      type="file"
                      accept=".csv,.json"
                      onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                      required
                      className="w-full rounded-md border border-[#DCE2E7] bg-white px-3 py-2.5 text-sm text-[#53616E] file:mr-3 file:rounded file:border-0 file:bg-[#EAF0F4] file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-[#315E79]"
                    />
                    {selectedFile && (
                      <p className="mt-2 text-xs text-[#53616E]">
                        Selected: {selectedFile.name}
                      </p>
                    )}
                  </div>

                  {uploadMessage && (
                    <p className="md:col-span-2 rounded-md bg-[#EAF5EF] p-3 text-sm text-[#438264]">
                      {uploadMessage}
                    </p>
                  )}

                  {uploadError && (
                    <p className="md:col-span-2 rounded-md bg-[#FCEEEE] p-3 text-sm text-[#B44B4B]">
                      {uploadError}
                    </p>
                  )}

                  <div className="md:col-span-2">
                    <button
                      type="submit"
                      disabled={uploadingDataset || factories.length === 0 || !selectedFile}
                      className="rounded-md bg-[#24485F] px-5 py-2.5 text-sm font-medium text-white transition hover:bg-[#19394E] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {uploadingDataset ? 'Uploading...' : 'Upload Dataset'}
                    </button>
                  </div>

                </form>
              </div>

              <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                  <div>
                    <h2 className="text-base font-semibold text-[#263746]">
                      Uploaded Datasets
                    </h2>
                    <p className="mt-1 text-xs text-[#82909C]">
                      Datasets uploaded by your company.
                    </p>
                  </div>

                  <input
                    type="text"
                    value={datasetSearch}
                    onChange={(event) => setDatasetSearch(event.target.value)}
                    placeholder="Search datasets..."
                    className="w-full rounded-md border border-[#DCE2E7] px-3 py-2 text-sm outline-none focus:border-[#315E79] sm:w-64"
                  />
                </div>

                {datasetsLoading ? (
                  <p className="py-10 text-center text-sm text-[#89949E]">
                    Loading datasets...
                  </p>
                ) : datasetsError ? (
                  <p className="rounded-md bg-[#FCEEEE] p-4 text-sm text-[#B44B4B]">
                    {datasetsError}
                  </p>
                ) : uploadedDatasets.filter((dataset) => {
                  const search = datasetSearch.toLowerCase()
                  const factoryName = factories.find(
                    (factory) => factory.id === dataset.factory_id
                  )?.name || ''

                  return (
                    dataset.filename.toLowerCase().includes(search) ||
                    dataset.dataset_type.toLowerCase().includes(search) ||
                    factoryName.toLowerCase().includes(search)
                  )
                }).length === 0 ? (
                  <p className="py-10 text-center text-sm text-[#89949E]">
                    {uploadedDatasets.length === 0
                      ? 'No datasets uploaded yet.'
                      : 'No datasets match your search.'}
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-[#E5E9ED] text-[#82909C]">
                          <th className="pb-3 pr-4">FILE NAME</th>
                          <th className="pb-3 pr-4">TYPE</th>
                          <th className="pb-3 pr-4">FACTORY</th>
                          <th className="pb-3 pr-4">RECORDS</th>
                          <th className="pb-3 pr-4">UPLOAD DATE</th>
                          <th className="pb-3">ACTION</th>
                        </tr>
                      </thead>

                      <tbody>
                        {uploadedDatasets
                          .filter((dataset) => {
                            const search = datasetSearch.toLowerCase()
                            const factoryName = factories.find(
                              (factory) => factory.id === dataset.factory_id
                            )?.name || ''

                            return (
                              dataset.filename.toLowerCase().includes(search) ||
                              dataset.dataset_type.toLowerCase().includes(search) ||
                              factoryName.toLowerCase().includes(search)
                            )
                          })
                          .map((dataset) => (
                            <tr
                              key={dataset.dataset_id}
                              className="border-b border-[#F0F2F4] last:border-0"
                            >
                              <td className="py-4 pr-4 font-medium text-[#52616D]">
                                {dataset.filename}
                              </td>

                              <td className="py-4 pr-4 text-[#778590]">
                                {dataset.dataset_type.replaceAll('_', ' ')}
                              </td>

                              <td className="py-4 pr-4 text-[#778590]">
                                {factories.find(
                                  (factory) => factory.id === dataset.factory_id
                                )?.name || `Factory #${dataset.factory_id}`}
                              </td>

                              <td className="py-4 pr-4 text-[#778590]">
                                {dataset.records_count.toLocaleString()}
                              </td>

                              <td className="py-4 pr-4 text-[#778590]">
                                {new Date(dataset.created_at).toLocaleDateString()}
                              </td>

                              <td className="py-4">
                                <button
                                  type="button"
                                  disabled={datasetDetailsLoading}
                                  onClick={async () => {
                                    setDatasetDetailsLoading(true)
                                    setSelectedDataset(null)

                                    try {
                                      const response = await api.get(
                                        `/data-upload/${dataset.dataset_id}`
                                      )
                                      setSelectedDataset(response.data)
                                    } catch (error) {
                                      const message = (
                                        error as { response?: { data?: { detail?: string } } }
                                      ).response?.data?.detail

                                      setDatasetsError(
                                        message || 'Could not load dataset details.'
                                      )
                                    } finally {
                                      setDatasetDetailsLoading(false)
                                    }
                                  }}
                                  className="rounded-md border border-[#DCE2E7] px-3 py-1.5 text-xs font-medium text-[#315E79] hover:bg-[#EAF0F4] disabled:opacity-50"
                                >
                                  View Details
                                </button>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {datasetDetailsLoading && (
                <p className="text-center text-sm text-[#82909C]">
                  Loading dataset details...
                </p>
              )}

              {selectedDataset && (
                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <h2 className="text-base font-semibold text-[#263746]">
                        Dataset Details
                      </h2>
                      <p className="mt-1 text-xs text-[#82909C]">
                        {selectedDataset.filename}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => setSelectedDataset(null)}
                      className="rounded-md border border-[#DCE2E7] px-3 py-1.5 text-xs text-[#53616E] hover:bg-[#F5F7F8]"
                    >
                      Close
                    </button>
                  </div>

                  <p className="mb-4 text-xs text-[#778590]">
                    Records: {selectedDataset.records_count.toLocaleString()}
                  </p>

                  {selectedDataset.columns && selectedDataset.records && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-[#E5E9ED] text-[#82909C]">
                            {selectedDataset.columns.map((column) => (
                              <th key={column} className="pb-3 pr-4">
                                {column}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {selectedDataset.records.slice(0, 20).map((record, index) => (
                            <tr key={index} className="border-b border-[#F0F2F4]">
                              {selectedDataset.columns!.map((column) => (
                                <td key={column} className="py-3 pr-4 text-[#53616E]">
                                  {String(record[column] ?? 'â€”')}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>

                      {selectedDataset.records.length > 20 && (
                        <p className="mt-3 text-xs text-[#89949E]">
                          Showing the first 20 records.
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

                       </section>
          ) : activePage === 'AI Predictions' ? (
            <section className="space-y-6">

              {/* Page Header */}
              <div>
                <div className="flex items-center gap-2">
                  <BrainCircuit size={22} className="text-[#416F85]" />
                  <h1 className="text-2xl font-semibold tracking-tight text-[#263746]">
                    AI Predictions
                  </h1>
                </div>

                <p className="mt-2 text-sm text-[#82909C]">
                  Review recorded AI prediction results from your datasets.
                </p>
              </div>

              {/* Statistics */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">

                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <p className="text-sm text-[#82909C]">Total Predictions</p>
                  <p className="mt-2 text-2xl font-semibold text-[#263746]">
                    {predictions.length.toLocaleString()}
                  </p>
                </div>

                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <p className="text-sm text-[#82909C]">Labeled Predictions</p>
                  <p className="mt-2 text-2xl font-semibold text-[#263746]">
                    {predictions.filter(
                      (prediction) => prediction.prediction_label
                    ).length.toLocaleString()}
                  </p>
                </div>

                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <p className="text-sm text-[#82909C]">Models Used</p>
                  <p className="mt-2 text-2xl font-semibold text-[#263746]">
                    {new Set(
                      predictions.map((prediction) => prediction.model_name)
                    ).size.toLocaleString()}
                  </p>
                </div>

              </div>

              {/* Loading */}
              {predictionsLoading && (
                <div className="rounded-lg border border-[#E5E9ED] bg-white p-8 text-center">
                  <p className="text-sm text-[#82909C]">
                    Loading AI predictions...
                  </p>
                </div>
              )}

              {/* Error */}
              {!predictionsLoading && predictionsError && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-5">
                  <p className="text-sm text-red-700">
                    {predictionsError}
                  </p>
                </div>
              )}

              {/* Predictions Table */}
              {!predictionsLoading && !predictionsError && (
                <div className="overflow-hidden rounded-lg border border-[#E5E9ED] bg-white">

                  <div className="border-b border-[#E5E9ED] p-5">
                    <h2 className="text-base font-semibold text-[#263746]">
                      Prediction History
                    </h2>
                    <p className="mt-1 text-xs text-[#82909C]">
                      Recorded prediction results from the backend.
                    </p>
                  </div>

                  {predictions.length === 0 ? (
                    <div className="p-10 text-center">
                      <BrainCircuit
                        size={32}
                        className="mx-auto text-[#A0AAB3]"
                      />
                      <p className="mt-3 text-sm font-medium text-[#53616E]">
                        No predictions available
                      </p>
                      <p className="mt-1 text-xs text-[#89949E]">
                        Prediction results will appear here when they are recorded.
                      </p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-sm">

                        <thead>
                          <tr className="border-b border-[#E5E9ED] bg-[#F8FAFB] text-xs text-[#82909C]">
                            <th className="px-5 py-3">Date</th>
                            <th className="px-5 py-3">Model</th>
                            <th className="px-5 py-3">Prediction</th>
                            <th className="px-5 py-3">Confidence Score</th>
                            <th className="px-5 py-3">Dataset ID</th>
                            <th className="px-5 py-3">Details</th>
                          </tr>
                        </thead>

                        <tbody>
                          {predictions.map((prediction) => (
                            <tr
                              key={prediction.id}
                              className="border-b border-[#F0F2F4] hover:bg-[#FAFBFC]"
                            >
                              <td className="whitespace-nowrap px-5 py-4 text-xs text-[#53616E]">
                                {new Date(prediction.created_at).toLocaleString()}
                              </td>

                              <td className="px-5 py-4 text-xs font-medium text-[#263746]">
                                {prediction.model_name}
                                {prediction.model_version && (
                                  <p className="mt-1 text-[#89949E]">
                                    Version {prediction.model_version}
                                  </p>
                                )}
                              </td>

                              <td className="px-5 py-4">
                                <span className="rounded-md bg-[#EFF4F6] px-2.5 py-1 text-xs font-medium text-[#416F85]">
                                  {prediction.prediction_label || 'Not specified'}
                                </span>
                              </td>

                              <td className="px-5 py-4 text-xs text-[#53616E]">
                                {prediction.confidence_score !== null
                                  ? prediction.confidence_score
                                  : 'Not available'}
                              </td>

                              <td className="px-5 py-4 text-xs text-[#53616E]">
                                #{prediction.uploaded_dataset_id}
                              </td>

                              <td className="px-5 py-4">
                                <button
                                  type="button"
                                  onClick={() =>
                                    setSelectedPrediction(prediction)
                                  }
                                  className="rounded-md border border-[#DCE2E7] px-3 py-1.5 text-xs font-medium text-[#416F85] hover:bg-[#F4F7F8]"
                                >
                                  View Details
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>

                      </table>
                    </div>
                  )}

                </div>
              )}

              {/* Selected Prediction Details */}
              {selectedPrediction && (
                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">

                  <div className="mb-5 flex items-center justify-between">
                    <div>
                      <h2 className="text-base font-semibold text-[#263746]">
                        Prediction Details
                      </h2>
                      <p className="mt-1 text-xs text-[#82909C]">
                        Prediction ID: #{selectedPrediction.id}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => setSelectedPrediction(null)}
                      className="rounded-md border border-[#DCE2E7] px-3 py-1.5 text-xs text-[#53616E] hover:bg-[#F5F7F8]"
                    >
                      Close
                    </button>
                  </div>

                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">

                    <div>
                      <p className="text-xs text-[#82909C]">Company ID</p>
                      <p className="mt-1 text-sm text-[#263746]">
                        {selectedPrediction.company_id}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-[#82909C]">Factory ID</p>
                      <p className="mt-1 text-sm text-[#263746]">
                        {selectedPrediction.factory_id}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-[#82909C]">Dataset ID</p>
                      <p className="mt-1 text-sm text-[#263746]">
                        {selectedPrediction.uploaded_dataset_id}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-[#82909C]">Record Index</p>
                      <p className="mt-1 text-sm text-[#263746]">
                        {selectedPrediction.record_index ?? 'Not specified'}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-[#82909C]">Model</p>
                      <p className="mt-1 text-sm text-[#263746]">
                        {selectedPrediction.model_name}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-[#82909C]">Created At</p>
                      <p className="mt-1 text-sm text-[#263746]">
                        {new Date(selectedPrediction.created_at).toLocaleString()}
                      </p>
                    </div>

                  </div>

                  <div className="mt-6 space-y-4">

                    <div>
                      <h3 className="mb-2 text-sm font-semibold text-[#263746]">
                        SHAP Explanation
                      </h3>
                      <pre className="overflow-x-auto rounded-md bg-[#F6F8F9] p-4 text-xs text-[#53616E]">
                        {selectedPrediction.shap_explanation
                          ? JSON.stringify(selectedPrediction.shap_explanation, null, 2)
                          : 'No SHAP explanation available.'}
                      </pre>
                    </div>

                    <div>
                      <h3 className="mb-2 text-sm font-semibold text-[#263746]">
                        Prediction Output
                      </h3>
                      <pre className="overflow-x-auto rounded-md bg-[#F6F8F9] p-4 text-xs text-[#53616E]">
                        {selectedPrediction.prediction_output
                          ? JSON.stringify(selectedPrediction.prediction_output, null, 2)
                          : 'No prediction output available.'}
                      </pre>
                    </div>

                  </div>
                </div>
              )}

                      </section>
          ) : activePage === 'Factories' ? (
            <section>
              <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
                <div>
                  <p className="text-xs font-medium text-[#82909C]">
                    INFRASTRUCTURE MANAGEMENT
                  </p>
                  <h1 className="mt-2 text-2xl font-semibold tracking-tight">
                    Factories
                  </h1>
                  <p className="mt-1 text-sm text-[#82909C]">
                    View and manage registered factories.
                  </p>
                </div>

                {(currentUser?.role_name === 'Admin' ||
                  currentUser?.role_name === 'Super Admin') && (
                  <button
                    onClick={openFactoryForm}
                    className="rounded-md bg-[#24485F] px-4 py-2.5 text-sm font-medium text-white hover:bg-[#19394E]"
                  >
                    + Add Factory
                  </button>
                )}
              </div>

              <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <p className="text-xs font-medium text-[#7C8995]">
                    Active Factories
                  </p>
                  <p className="mt-3 text-3xl font-semibold">
                    {factories.length}
                  </p>
                </div>

                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <p className="text-xs font-medium text-[#7C8995]">
                    Your Role
                  </p>
                  <p className="mt-3 text-lg font-semibold">
                    {currentUser?.role_name || 'Unknown'}
                  </p>
                </div>
              </div>

              {factoryMessage && (
                <div className="mb-4 rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-700">
                  {factoryMessage}
                </div>
              )}

              {factoryError && (
                <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {factoryError}
                </div>
              )}

              {factoryFormOpen && (
                <div className="mb-6 rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <h2 className="mb-5 text-lg font-semibold text-[#263746]">
                    {editingFactory ? 'Edit Factory' : 'Add New Factory'}
                  </h2>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div>
                      <label className="mb-2 block text-sm font-medium text-[#53616E]">
                        Factory Name
                      </label>
                      <input
                        value={factoryName}
                        onChange={(e) => setFactoryName(e.target.value)}
                        placeholder="Enter factory name"
                        className="w-full rounded-md border border-[#DDE3E8] px-3 py-2.5 text-sm outline-none focus:border-[#45677D]"
                      />
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-medium text-[#53616E]">
                        Location
                      </label>
                      <input
                        value={factoryLocation}
                        onChange={(e) => setFactoryLocation(e.target.value)}
                        placeholder="Enter factory location"
                        className="w-full rounded-md border border-[#DDE3E8] px-3 py-2.5 text-sm outline-none focus:border-[#45677D]"
                      />
                    </div>

                    {currentUser?.role_name === 'Super Admin' &&
                      !editingFactory && (
                        <div className="md:col-span-2">
                          <label className="mb-2 block text-sm font-medium text-[#53616E]">
                            Company
                          </label>
                          <select
                            value={factoryCompanyId}
                            onChange={(e) =>
                              setFactoryCompanyId(e.target.value)
                            }
                            className="w-full rounded-md border border-[#DDE3E8] bg-white px-3 py-2.5 text-sm outline-none focus:border-[#45677D]"
                          >
                            <option value="">Select a company</option>
                            {companies.map((company) => (
                              <option key={company.id} value={company.id}>
                                {company.name}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}
                  </div>

                  <div className="mt-5 flex gap-2">
                    <button
                      onClick={handleSaveFactory}
                      disabled={factorySaving}
                      className="rounded-md bg-[#24485F] px-4 py-2.5 text-sm font-medium text-white hover:bg-[#19394E] disabled:opacity-50"
                    >
                      {factorySaving
                        ? 'Saving...'
                        : editingFactory
                          ? 'Save Changes'
                          : 'Create Factory'}
                    </button>

                    <button
                      onClick={() => {
                        setFactoryFormOpen(false)
                        setEditingFactory(null)
                        setFactoryError('')
                      }}
                      className="rounded-md border border-[#DDE3E8] px-4 py-2.5 text-sm font-medium text-[#53616E] hover:bg-[#F6F8F9]"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              <div className="mb-4">
                <input
                  value={factorySearch}
                  onChange={(e) => setFactorySearch(e.target.value)}
                  placeholder="Search factories by name or location..."
                  className="w-full rounded-md border border-[#DDE3E8] bg-white px-4 py-3 text-sm outline-none focus:border-[#45677D]"
                />
              </div>

              <div className="overflow-hidden rounded-lg border border-[#E5E9ED] bg-white">
                {factoriesLoading ? (
                  <p className="p-8 text-center text-sm text-[#82909C]">
                    Loading factories...
                  </p>
                ) : factories.filter((factory) =>
                    `${factory.name} ${factory.location || ''}`
                      .toLowerCase()
                      .includes(factorySearch.toLowerCase())
                  ).length === 0 ? (
                  <p className="p-8 text-center text-sm text-[#82909C]">
                    No factories found.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left">
                      <thead className="bg-[#F6F8F9]">
                        <tr className="text-xs text-[#82909C]">
                          <th className="px-5 py-4 font-medium">Factory</th>
                          <th className="px-5 py-4 font-medium">Location</th>
                          <th className="px-5 py-4 font-medium">Company ID</th>
                          {(currentUser?.role_name === 'Admin' ||
                            currentUser?.role_name === 'Super Admin') && (
                            <th className="px-5 py-4 font-medium">Actions</th>
                          )}
                        </tr>
                      </thead>

                      <tbody>
                        {factories
                          .filter((factory) =>
                            `${factory.name} ${factory.location || ''}`
                              .toLowerCase()
                              .includes(factorySearch.toLowerCase())
                          )
                          .map((factory) => (
                            <tr
                              key={factory.id}
                              className="border-t border-[#E5E9ED] text-sm"
                            >
                              <td className="px-5 py-4 font-medium text-[#263746]">
                                {factory.name}
                              </td>
                              <td className="px-5 py-4 text-[#53616E]">
                                {factory.location || 'Not specified'}
                              </td>
                              <td className="px-5 py-4 text-[#53616E]">
                                {factory.company_id}
                              </td>

                              {(currentUser?.role_name === 'Admin' ||
                                currentUser?.role_name === 'Super Admin') && (
                                <td className="px-5 py-4">
                                  <div className="flex gap-3">
                                    <button
                                      onClick={() =>
                                        openFactoryEditForm(factory)
                                      }
                                      className="font-medium text-[#45677D] hover:underline"
                                    >
                                      Edit
                                    </button>
                                    <button
                                      onClick={() =>
                                        handleDeleteFactory(factory)
                                      }
                                      className="font-medium text-red-600 hover:underline"
                                    >
                                      Deactivate
                                    </button>
                                  </div>
                                </td>
                              )}
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
                       </section>
          ) : activePage === 'Users & Roles' ? (
            <section className="space-y-6">
              <div>
                <h1 className="text-2xl font-semibold tracking-tight">
                  Users & Roles
                </h1>

                <p className="mt-1 text-sm text-[#82909C]">
                  Manage platform users and their access permissions.
                </p>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <p className="text-sm text-[#82909C]">Total Users</p>
                  <h2 className="mt-2 text-2xl font-semibold">
                    {users.length}
                  </h2>
                </div>

                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <p className="text-sm text-[#82909C]">Active Users</p>
                  <h2 className="mt-2 text-2xl font-semibold text-green-700">
                    {users.filter((user) => user.is_active).length}
                  </h2>
                </div>

                <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                  <p className="text-sm text-[#82909C]">Inactive Users</p>
                  <h2 className="mt-2 text-2xl font-semibold text-red-600">
                    {users.filter((user) => !user.is_active).length}
                  </h2>
                </div>
              </div>

              {usersError && (
                <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {usersError}
                </div>
              )}

              {usersMessage && (
                <div className="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-700">
                  {usersMessage}
                </div>
              )}

              <div className="flex flex-col justify-between gap-3 sm:flex-row">
                <input
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  placeholder="Search by username or email..."
                  className="w-full rounded-md border border-[#DDE3E8] bg-white px-4 py-3 text-sm outline-none focus:border-[#45677D] sm:max-w-md"
                />

                <div className="flex gap-2">
                  <select
                    value={userStatusFilter}
                    onChange={(e) => setUserStatusFilter(e.target.value)}
                    className="rounded-md border border-[#DDE3E8] bg-white px-3 py-2 text-sm"
                  >
                    <option value="All">All Users</option>
                    <option value="Active">Active</option>
                    <option value="Inactive">Inactive</option>
                  </select>

                  {currentUser?.role_name === 'Admin' ||
                  currentUser?.role_name === 'Super Admin' ? (
                    <button
                      onClick={openUserForm}
                      className="rounded-md bg-[#24485F] px-4 py-2 text-sm font-medium text-white hover:bg-[#19394E]"
                    >
                      Add User
                    </button>
                  ) : null}
                </div>
              </div>

              <div className="overflow-hidden rounded-lg border border-[#E5E9ED] bg-white">
                {usersLoading ? (
                  <p className="p-8 text-center text-sm text-[#82909C]">
                    Loading users...
                  </p>
                ) : users.filter((user) => {
                    const matchesSearch =
                      `${user.username} ${user.email}`
                        .toLowerCase()
                        .includes(userSearch.toLowerCase())

                    const matchesStatus =
                      userStatusFilter === 'All' ||
                      (userStatusFilter === 'Active' && user.is_active) ||
                      (userStatusFilter === 'Inactive' && !user.is_active)

                    return matchesSearch && matchesStatus
                  }).length === 0 ? (
                  <p className="p-8 text-center text-sm text-[#82909C]">
                    No users found.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left">
                      <thead className="bg-[#F6F8F9]">
                        <tr className="text-xs text-[#82909C]">
                          <th className="px-5 py-4 font-medium">Username</th>
                          <th className="px-5 py-4 font-medium">Email</th>
                          <th className="px-5 py-4 font-medium">Role</th>
                          <th className="px-5 py-4 font-medium">Company ID</th>
                          <th className="px-5 py-4 font-medium">Status</th>
                          {(currentUser?.role_name === 'Admin' ||
                            currentUser?.role_name === 'Super Admin') && (
                            <th className="px-5 py-4 font-medium">Actions</th>
                          )}
                        </tr>
                      </thead>

                      <tbody>
                        {users
                          .filter((user) => {
                            const matchesSearch =
                              `${user.username} ${user.email}`
                                .toLowerCase()
                                .includes(userSearch.toLowerCase())

                            const matchesStatus =
                              userStatusFilter === 'All' ||
                              (userStatusFilter === 'Active' && user.is_active) ||
                              (userStatusFilter === 'Inactive' && !user.is_active)

                            return matchesSearch && matchesStatus
                          })
                          .map((user) => {
                            const userRole = roles.find(
                              (role) => role.id === user.role_id
                            )

                            return (
                              <tr
                                key={user.id}
                                className="border-t border-[#E5E9ED] text-sm"
                              >
                                <td className="px-5 py-4 font-medium text-[#263746]">
                                  {user.username}
                                </td>

                                <td className="px-5 py-4 text-[#53616E]">
                                  {user.email}
                                </td>

                                <td className="px-5 py-4 text-[#53616E]">
                                  {userRole?.name || 'Unknown Role'}
                                </td>

                                <td className="px-5 py-4 text-[#53616E]">
                                  {user.company_id}
                                </td>

                                <td className="px-5 py-4">
                                  <span
                                    className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                                      user.is_active
                                        ? 'bg-green-50 text-green-700'
                                        : 'bg-red-50 text-red-700'
                                    }`}
                                  >
                                    {user.is_active ? 'Active' : 'Inactive'}
                                  </span>
                                </td>

                                {(currentUser?.role_name === 'Admin' ||
                                  currentUser?.role_name === 'Super Admin') && (
                                  <td className="px-5 py-4">
                                    <div className="flex gap-3">
                                      <button
                                        onClick={() => openUserEditForm(user)}
                                        disabled={!user.is_active}
                                        className="font-medium text-[#45677D] hover:underline disabled:cursor-not-allowed disabled:opacity-40"
                                      >
                                        Edit
                                      </button>

                                      <button
                                        onClick={() => handleDeactivateUser(user)}
                                        disabled={
                                          !user.is_active ||
                                          user.id === currentUser?.id
                                        }
                                        className="font-medium text-red-600 hover:underline disabled:cursor-not-allowed disabled:opacity-40"
                                      >
                                        Deactivate
                                      </button>
                                    </div>
                                  </td>
                                )}
                              </tr>
                            )
                          })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              <div className="rounded-lg border border-[#E5E9ED] bg-white p-5">
                <h2 className="text-base font-semibold text-[#263746]">
                  Available Roles
                </h2>

                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {roles.map((role) => (
                    <div
                      key={role.id}
                      className="rounded-md border border-[#E5E9ED] p-4"
                    >
                      <h3 className="font-medium text-[#263746]">
                        {role.name}
                      </h3>

                      <p className="mt-1 text-xs text-[#82909C]">
                        {role.description || 'No description available.'}
                      </p>
                    </div>
                  ))}
                </div>
                           </div>

              {/* Add / Edit User Form */}
              {userFormOpen && (
                <div className="rounded-lg border border-[#E5E9ED] bg-white p-6">
                  <div className="mb-5">
                    <h2 className="text-lg font-semibold text-[#263746]">
                      {editingUser ? 'Edit User' : 'Add New User'}
                    </h2>

                    <p className="mt-1 text-sm text-[#82909C]">
                      {editingUser
                        ? 'Update the user account information.'
                        : 'Create a new platform user account.'}
                    </p>
                  </div>

                  <form
                    onSubmit={(e) => {
                      e.preventDefault()
                      void handleSaveUser()
                    }}
                    className="grid gap-4 sm:grid-cols-2"
                  >
                    <div>
                      <label className="mb-2 block text-sm font-medium text-[#53616E]">
                        Username
                      </label>
                      <input
                        type="text"
                        value={userUsername}
                        onChange={(e) => setUserUsername(e.target.value)}
                        minLength={3}
                        maxLength={50}
                        required
                        className="w-full rounded-md border border-[#DDE3E8] px-3 py-2.5 text-sm outline-none focus:border-[#45677D]"
                        placeholder="Enter username"
                      />
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-medium text-[#53616E]">
                        Email
                      </label>
                      <input
                        type="email"
                        value={userEmail}
                        onChange={(e) => setUserEmail(e.target.value)}
                        required
                        className="w-full rounded-md border border-[#DDE3E8] px-3 py-2.5 text-sm outline-none focus:border-[#45677D]"
                        placeholder="user@example.com"
                      />
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-medium text-[#53616E]">
                        {editingUser
                          ? 'New Password (optional)'
                          : 'Password'}
                      </label>
                      <input
                        type="password"
                        value={userPassword}
                        onChange={(e) => setUserPassword(e.target.value)}
                        minLength={8}
                        required={!editingUser}
                        className="w-full rounded-md border border-[#DDE3E8] px-3 py-2.5 text-sm outline-none focus:border-[#45677D]"
                        placeholder={
                          editingUser
                            ? 'Leave blank to keep current password'
                            : 'At least 8 characters'
                        }
                      />
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-medium text-[#53616E]">
                        Role
                      </label>
                      <select
                        value={userRoleId}
                        onChange={(e) => setUserRoleId(e.target.value)}
                        required
                        className="w-full rounded-md border border-[#DDE3E8] bg-white px-3 py-2.5 text-sm outline-none focus:border-[#45677D]"
                      >
                        <option value="">Select a role</option>
                        {roles
                          .filter(
                            (role) =>
                              currentUser?.role_name === 'Super Admin' ||
                              (role.name !== 'Admin' &&
                                role.name !== 'Super Admin')
                          )
                          .map((role) => (
                            <option key={role.id} value={role.id}>
                              {role.name}
                            </option>
                          ))}
                      </select>
                    </div>

                    {!editingUser &&
                      currentUser?.role_name === 'Super Admin' && (
                        <div>
                          <label className="mb-2 block text-sm font-medium text-[#53616E]">
                            Company
                          </label>
                          <select
                            value={userCompanyId}
                            onChange={(e) =>
                              setUserCompanyId(e.target.value)
                            }
                            required
                            className="w-full rounded-md border border-[#DDE3E8] bg-white px-3 py-2.5 text-sm outline-none focus:border-[#45677D]"
                          >
                            <option value="">Select a company</option>
                            {companies.map((company) => (
                              <option key={company.id} value={company.id}>
                                {company.name}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}

                    <div className="flex items-end gap-3 sm:col-span-2">
                      <button
                        type="submit"
                        disabled={usersSaving}
                        className="rounded-md bg-[#24485F] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#19394E] disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {usersSaving
                          ? 'Saving...'
                          : editingUser
                            ? 'Save Changes'
                            : 'Create User'}
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setUserFormOpen(false)
                          setEditingUser(null)
                        }}
                        disabled={usersSaving}
                        className="rounded-md border border-[#DDE3E8] px-5 py-2.5 text-sm font-medium text-[#53616E] hover:bg-[#F6F8F9]"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}
            </section>
          ) : (
            <>

          <div className="mb-7 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div>
              <p className="text-xs font-medium text-[#82909C]">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: '2-digit', year: 'numeric' }).toUpperCase()}
              </p>

              <h1 className="mt-2 text-2xl font-semibold tracking-tight">
                Security Overview
              </h1>

              <p className="mt-1 text-sm text-[#82909C]">
                Monitor your industrial infrastructure and security activity.
              </p>
            </div>

            <div className="flex gap-2">
              <div className="flex items-center gap-2 rounded-md border border-[#DDE3E8] bg-white px-3 py-2.5">
                <CalendarDays size={15} className="text-[#53616E]" />
                <select
                  value={selectedTimeRange}
                  onChange={(event) => setSelectedTimeRange(
                    event.target.value as '24h' | '7d' | '30d' | 'all'
                  )}
                  className="bg-transparent text-xs font-medium text-[#53616E] outline-none"
                  aria-label="Dashboard time range"
                >
                  <option value="24h">Last 24 hours</option>
                  <option value="7d">Last 7 days</option>
                  <option value="30d">Last 30 days</option>
                  <option value="all">All time</option>
                </select>
              </div>

              <button
                type="button"
                onClick={handleExportReport}
                disabled={!dashboardStats}
                className="flex items-center gap-2 rounded-md bg-[#24485F] px-3 py-2.5 text-xs font-medium text-white hover:bg-[#19394E] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Download size={15} />
                Export Report
              </button>
            </div>
          </div>

          <div className="mb-7 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => {
              const Icon = stat.icon

              return (
                <div
                  key={stat.label}
                  className="rounded-lg border border-[#E5E9ED] bg-white p-5"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium text-[#7C8995]">
                      {stat.label}
                    </p>

                    <div className="rounded-md bg-[#F0F4F6] p-2 text-[#45677D]">
                      <Icon size={18} />
                    </div>
                  </div>

                  <p className="mt-4 text-3xl font-semibold tracking-tight">
                    {stat.value}
                  </p>

                  <p className="mt-2 text-[11px] text-[#89949E]">
                    {stat.change}
                  </p>
                </div>
              )
            })}
          </div>

          <div className="mb-6 grid grid-cols-1 gap-5 xl:grid-cols-3">

            <section className="rounded-lg border border-[#E5E9ED] bg-white p-5 xl:col-span-2">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold">
                    Network Activity
                  </h3>
                  <p className="mt-1 text-xs text-[#89949E]">
                    {trafficChartData.length > 0
                      ? 'Actual network events during the selected period'
                      : 'No network events recorded during this period'}
                  </p>
                </div>

                <button className="rounded-md p-2 text-[#89949E] hover:bg-[#F4F6F8]">
                  <MoreHorizontal size={19} />
                </button>
              </div>

              <div className="h-[270px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trafficChartData}>
                    <defs>
                      <linearGradient id="trafficFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#4F8195" stopOpacity={0.2} />
                        <stop offset="100%" stopColor="#4F8195" stopOpacity={0} />
                      </linearGradient>
                    </defs>

                    <CartesianGrid stroke="#EDF0F2" vertical={false} />

                    <XAxis
                      dataKey="time"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#8A96A0', fontSize: 11 }}
                    />

                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#8A96A0', fontSize: 11 }}
                    />

                    <Tooltip />

                    <Area
                      type="monotone"
                      dataKey="events"
                      stroke="#416F85"
                      strokeWidth={2}
                      fill="url(#trafficFill)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="rounded-lg border border-[#E5E9ED] bg-white p-5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold">
                    Dataset Distribution
                  </h3>
                  <p className="mt-1 text-xs text-[#89949E]">
                    Records by dataset type
                  </p>
                </div>

                <MoreHorizontal size={19} className="text-[#89949E]" />
              </div>

              <div className="relative mt-3 h-[190px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={datasetData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={55}
                      outerRadius={78}
                      paddingAngle={3}
                    >
                      {datasetData.map((entry, index) => (
                        <Cell
                          key={entry.name}
                          fill={datasetColors[index % datasetColors.length]}
                        />
                      ))}
                    </Pie>

                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="space-y-3">
                {datasetData.map((item, index) => (
                  <div
                    key={item.name}
                    className="flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2 text-[#687784]">
                      <span
                        className="h-2.5 w-2.5 rounded-sm"
                        style={{ background: datasetColors[index % datasetColors.length] }}
                      />
                      {item.name}
                    </div>

                    <span className="font-semibold">
                      {item.value} records
                    </span>
                  </div>
                ))}
              </div>
            </section>

          </div>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">

            <section className="rounded-lg border border-[#E5E9ED] bg-white p-5 xl:col-span-2">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold">
                    Recent Security Events
                  </h3>
                  <p className="mt-1 text-xs text-[#89949E]">
                    Latest recorded network events
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setActivePage('Network Monitoring')}
                  className="text-xs font-medium text-[#416F85] hover:underline"
                >
                  View all
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full min-w-[520px] text-left text-xs">
                  <thead>
                    <tr className="border-b border-[#EDF0F2] text-[#8A96A0]">
                      <th className="pb-3 font-medium">PROTOCOL</th>
                      <th className="pb-3 font-medium">SOURCE</th>
                      <th className="pb-3 font-medium">DESTINATION</th>
                      <th className="pb-3 font-medium">TIME</th>
                    </tr>
                  </thead>

                  <tbody>
                    {networkEventsLoading ? (
                      <tr>
                        <td colSpan={4} className="py-8 text-center text-[#89949E]">
                          Loading network events...
                        </td>
                      </tr>
                    ) : networkEvents.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="py-8 text-center text-[#89949E]">
                          No network events recorded yet.
                        </td>
                      </tr>
                    ) : (
                      networkEvents.slice(0, 5).map((event) => {
                        const eventDate = event.event_time || event.created_at

                        return (
                          <tr key={event.id} className="border-b border-[#F0F2F4]">
                            <td className="py-4 font-semibold">
                              {event.protocol}
                            </td>

                            <td className="py-4 text-[#778590]">
                              {event.source_ip}
                            </td>

                            <td className="py-4 text-[#778590]">
                              {event.destination_ip}
                            </td>

                            <td className="py-4 text-[#89949E]">
                              {eventDate
                                ? new Date(eventDate).toLocaleString()
                                : 'Unknown'}
                            </td>
                          </tr>
                        )
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-lg border border-[#E5E9ED] bg-white p-5">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold">System Health</h3>
                  <p className="mt-1 text-xs text-[#89949E]">
                    Live platform status
                  </p>
                </div>

                <span className={`rounded px-2 py-1 text-[10px] font-semibold ${
                  systemHealth?.status === 'Healthy'
                    ? 'bg-[#EAF5EF] text-[#438264]'
                    : systemHealth?.status === 'Degraded' ||
                      systemHealth?.status === 'Unavailable'
                      ? 'bg-[#FCEEEE] text-[#B54747]'
                      : 'bg-[#F5F7F8] text-[#89949E]'
                }`}>
                  {systemHealth?.status.toUpperCase() ?? 'CHECKING'}
                </span>
              </div>

              <div className="space-y-5">
                <div className="flex items-center gap-3">
                  <div className="rounded-md bg-[#EFF4F6] p-2 text-[#416F85]">
                    <Server size={17} />
                  </div>

                  <div className="flex-1">
                    <p className="text-xs font-medium">Backend API</p>
                    <p className="mt-1 text-[11px] text-[#89949E]">
                      {systemHealth?.status === 'Unavailable'
                        ? 'Service unavailable'
                        : systemHealth
                          ? 'Service responding'
                          : 'Checking service...'}
                    </p>
                  </div>

                  <span className={`h-2 w-2 rounded-full ${
                    systemHealth?.status === 'Unavailable'
                      ? 'bg-[#C65B5B]'
                      : systemHealth
                        ? 'bg-[#438C70]'
                        : 'bg-[#D6A75D]'
                  }`} />
                </div>

                <div className="flex items-center gap-3">
                  <div className="rounded-md bg-[#EFF4F6] p-2 text-[#416F85]">
                    <Database size={17} />
                  </div>

                  <div className="flex-1">
                    <p className="text-xs font-medium">Database</p>
                    <p className="mt-1 text-[11px] text-[#89949E]">
                      {systemHealth?.database === 'Connected'
                        ? 'Connection established'
                        : systemHealth?.database === 'Disconnected'
                          ? 'Connection failed'
                          : systemHealth?.database === 'Unknown'
                            ? 'Status unavailable'
                            : 'Checking connection...'}
                    </p>
                  </div>

                  <span className={`h-2 w-2 rounded-full ${
                    systemHealth?.database === 'Connected'
                      ? 'bg-[#438C70]'
                      : systemHealth?.database === 'Disconnected'
                        ? 'bg-[#C65B5B]'
                        : 'bg-[#D6A75D]'
                  }`} />
                </div>

                <div className="flex items-center gap-3">
                  <div className="rounded-md bg-[#EFF4F6] p-2 text-[#416F85]">
                    <BrainCircuit size={17} />
                  </div>

                  <div className="flex-1">
                    <p className="text-xs font-medium">ML Pipeline</p>
                    <p className="mt-1 text-[11px] text-[#89949E]">
                      {mlPipeline?.model_loaded
                        ? 'Model loaded and ready'
                        : mlPipeline?.status === 'Unavailable'
                          ? 'Status unavailable'
                          : mlPipeline?.message ?? 'Checking ML pipeline...'}
                    </p>
                  </div>

                  <span className={`h-2 w-2 rounded-full ${
                    mlPipeline?.model_loaded
                      ? 'bg-[#438C70]'
                      : mlPipeline?.status === 'Unavailable'
                        ? 'bg-[#C65B5B]'
                        : 'bg-[#D6A75D]'
                  }`} />
                </div>
              </div>

              <div className="mt-6 rounded-md bg-[#F5F7F8] p-3">
                <div className="flex items-center gap-2 text-xs font-medium text-[#52616D]">
                  <Clock3 size={14} />
                  Last system check
                </div>

                <p className="mt-2 text-[11px] text-[#89949E]">
                  {systemHealth?.last_check
                    ? new Date(systemHealth.last_check).toLocaleString()
                    : 'Awaiting health check'}
                </p>
              </div>
            </section>

          </div>

          <footer className="mt-8 flex flex-col justify-between gap-2 border-t border-[#E5E9ED] pt-5 text-[11px] text-[#9AA4AD] sm:flex-row">
            <span>Industrial Security Platform © 2026</span>
            <span>Live statistics · Data refreshed automatically</span>
          </footer>

          </>
          )}
        </div>
        {isGlobalSearchOpen && (
          <div
            className="fixed inset-0 z-[100] flex items-start justify-center bg-[#17232D]/45 px-4 pt-[12vh]"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) {
                setIsGlobalSearchOpen(false)
              }
            }}
          >
            <section
              role="dialog"
              aria-modal="true"
              aria-label="Global search"
              className="w-full max-w-[620px] overflow-hidden rounded-xl border border-[#E5E9ED] bg-white shadow-2xl"
            >
              <div className="flex items-center gap-3 border-b border-[#E5E9ED] px-5 py-4">
                <Search size={19} className="text-[#89939D]" />

                <input
                  autoFocus
                  type="text"
                  value={globalSearchQuery}
                  onChange={(event) => setGlobalSearchQuery(event.target.value)}
                  placeholder="Search users, factories, datasets, events..."
                  className="min-w-0 flex-1 bg-transparent text-sm text-[#263746] outline-none placeholder:text-[#A0AAB3]"
                />

                <button
                  type="button"
                  onClick={() => setIsGlobalSearchOpen(false)}
                  className="rounded border border-[#E5E9ED] px-2 py-1 text-[11px] text-[#89939D] hover:bg-[#F4F6F8]"
                >
                  ESC
                </button>
              </div>

              <div className="max-h-[60vh] overflow-y-auto p-3">
                {!searchTerm && (
                  <p className="px-3 py-8 text-center text-sm text-[#89939D]">
                    Start typing to search across your workspace.
                  </p>
                )}

                {searchTerm && globalSearchLoading && (
                  <p className="px-3 py-5 text-center text-sm text-[#89939D]">
                    Loading search data...
                  </p>
                )}

                {searchTerm && globalSearchResults.length === 0 && !globalSearchLoading && (
                  <p className="px-3 py-8 text-center text-sm text-[#89939D]">
                    No matching results found.
                  </p>
                )}

                {globalSearchResults.map((result) => (
                  <button
                    key={result.id}
                    type="button"
                    onClick={() => {
                      setActivePage(result.page)
                      setIsGlobalSearchOpen(false)
                      setGlobalSearchQuery('')
                    }}
                    className="flex w-full items-center justify-between gap-4 rounded-lg px-3 py-3 text-left transition hover:bg-[#F4F7F9]"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-[#263746]">
                        {result.title}
                      </p>
                      <p className="mt-1 truncate text-xs text-[#89939D]">
                        {result.subtitle}
                      </p>
                    </div>

                    <span className="shrink-0 rounded bg-[#EFF4F6] px-2 py-1 text-[10px] font-medium text-[#416F85]">
                      {result.category}
                    </span>
                  </button>
                ))}
              </div>

              <div className="border-t border-[#E5E9ED] px-5 py-3 text-[11px] text-[#89939D]">
                Search across available workspace data
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
