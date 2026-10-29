import Header from '../components/Header'

export default function AppLayout({ children }) {
  return (
    <div className="app-layout">
      <Header />
      <main className="main-content">{children}</main>
    </div>
  )
}
