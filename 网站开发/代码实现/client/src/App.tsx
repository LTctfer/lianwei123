import React, { Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout, Spin } from 'antd';
import { motion, AnimatePresence } from 'framer-motion';

import Header from './components/Layout/Header';
import Footer from './components/Layout/Footer';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import { useAuth } from './contexts/AuthContext';
import { useTheme } from './contexts/ThemeContext';

// 懒加载页面组件
const HomePage = React.lazy(() => import('./pages/Home/HomePage'));
const LoginPage = React.lazy(() => import('./pages/Auth/LoginPage'));
const RegisterPage = React.lazy(() => import('./pages/Auth/RegisterPage'));
const ProductsPage = React.lazy(() => import('./pages/Products/ProductsPage'));
const ProductDetailPage = React.lazy(() => import('./pages/Products/ProductDetailPage'));
const CartPage = React.lazy(() => import('./pages/Cart/CartPage'));
const CheckoutPage = React.lazy(() => import('./pages/Checkout/CheckoutPage'));
const ProfilePage = React.lazy(() => import('./pages/Profile/ProfilePage'));
const OrdersPage = React.lazy(() => import('./pages/Orders/OrdersPage'));
const AdminDashboard = React.lazy(() => import('./pages/Admin/AdminDashboard'));
const CommunityPage = React.lazy(() => import('./pages/Community/CommunityPage'));
const AnalyticsPage = React.lazy(() => import('./pages/Analytics/AnalyticsPage'));
const NotFoundPage = React.lazy(() => import('./pages/NotFound/NotFoundPage'));

const { Content } = Layout;

// 页面加载动画
const PageLoader: React.FC = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    minHeight: '60vh' 
  }}>
    <Spin size="large" tip="页面加载中..." />
  </div>
);

// 页面切换动画配置
const pageVariants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  in: {
    opacity: 1,
    y: 0,
  },
  out: {
    opacity: 0,
    y: -20,
  },
};

const pageTransition = {
  type: 'tween',
  ease: 'anticipate',
  duration: 0.3,
};

const App: React.FC = () => {
  const { user, loading } = useAuth();
  const { theme } = useTheme();

  if (loading) {
    return <PageLoader />;
  }

  return (
    <Layout className={`app-layout ${theme}`} style={{ minHeight: '100vh' }}>
      <Header />
      
      <Content style={{ flex: 1 }}>
        <AnimatePresence mode="wait">
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* 公共路由 */}
              <Route 
                path="/" 
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <HomePage />
                  </motion.div>
                } 
              />
              
              <Route 
                path="/login" 
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <LoginPage />
                  </motion.div>
                } 
              />
              
              <Route 
                path="/register" 
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <RegisterPage />
                  </motion.div>
                } 
              />

              {/* 产品相关路由 */}
              <Route 
                path="/products" 
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <ProductsPage />
                  </motion.div>
                } 
              />
              
              <Route 
                path="/products/:id" 
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <ProductDetailPage />
                  </motion.div>
                } 
              />

              {/* 购物车和结算 */}
              <Route 
                path="/cart" 
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <CartPage />
                  </motion.div>
                } 
              />

              {/* 需要登录的路由 */}
              <Route 
                path="/checkout" 
                element={
                  <ProtectedRoute>
                    <motion.div
                      initial="initial"
                      animate="in"
                      exit="out"
                      variants={pageVariants}
                      transition={pageTransition}
                    >
                      <CheckoutPage />
                    </motion.div>
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/profile" 
                element={
                  <ProtectedRoute>
                    <motion.div
                      initial="initial"
                      animate="in"
                      exit="out"
                      variants={pageVariants}
                      transition={pageTransition}
                    >
                      <ProfilePage />
                    </motion.div>
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/orders" 
                element={
                  <ProtectedRoute>
                    <motion.div
                      initial="initial"
                      animate="in"
                      exit="out"
                      variants={pageVariants}
                      transition={pageTransition}
                    >
                      <OrdersPage />
                    </motion.div>
                  </ProtectedRoute>
                } 
              />

              {/* 社区功能 */}
              <Route 
                path="/community" 
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <CommunityPage />
                  </motion.div>
                } 
              />

              {/* 管理员路由 */}
              <Route 
                path="/admin/*" 
                element={
                  <ProtectedRoute requiredRole="ADMIN">
                    <motion.div
                      initial="initial"
                      animate="in"
                      exit="out"
                      variants={pageVariants}
                      transition={pageTransition}
                    >
                      <AdminDashboard />
                    </motion.div>
                  </ProtectedRoute>
                } 
              />

              {/* 数据分析 */}
              <Route 
                path="/analytics" 
                element={
                  <ProtectedRoute requiredRole="ADMIN">
                    <motion.div
                      initial="initial"
                      animate="in"
                      exit="out"
                      variants={pageVariants}
                      transition={pageTransition}
                    >
                      <AnalyticsPage />
                    </motion.div>
                  </ProtectedRoute>
                } 
              />

              {/* 404页面 */}
              <Route 
                path="*" 
                element={
                  <motion.div
                    initial="initial"
                    animate="in"
                    exit="out"
                    variants={pageVariants}
                    transition={pageTransition}
                  >
                    <NotFoundPage />
                  </motion.div>
                } 
              />
            </Routes>
          </Suspense>
        </AnimatePresence>
      </Content>

      <Footer />
    </Layout>
  );
};

export default App;