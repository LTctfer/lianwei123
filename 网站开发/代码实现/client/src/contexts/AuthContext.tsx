import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { message } from 'antd';
import { authAPI } from '../services/api';

// 用户接口定义
interface User {
  id: number;
  username: string;
  email: string;
  role: 'USER' | 'ADMIN' | 'MODERATOR';
  status: 'ACTIVE' | 'INACTIVE' | 'BANNED';
  emailVerified: boolean;
  profile?: {
    firstName?: string;
    lastName?: string;
    avatar?: string;
    phone?: string;
  };
}

// 认证状态接口
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  accessToken: string | null;
  refreshToken: string | null;
}

// 认证动作类型
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; accessToken: string; refreshToken: string } }
  | { type: 'AUTH_FAILURE' }
  | { type: 'LOGOUT' }
  | { type: 'UPDATE_USER'; payload: User }
  | { type: 'SET_LOADING'; payload: boolean };

// 初始状态
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  accessToken: localStorage.getItem('accessToken'),
  refreshToken: localStorage.getItem('refreshToken'),
};

// 状态管理器
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
      };
    case 'AUTH_SUCCESS':
      localStorage.setItem('accessToken', action.payload.accessToken);
      localStorage.setItem('refreshToken', action.payload.refreshToken);
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        isLoading: false,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken,
      };
    case 'AUTH_FAILURE':
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        accessToken: null,
        refreshToken: null,
      };
    case 'LOGOUT':
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        accessToken: null,
        refreshToken: null,
      };
    case 'UPDATE_USER':
      return {
        ...state,
        user: action.payload,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    default:
      return state;
  }
}

// 认证上下文接口
interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  updateUser: (userData: Partial<User>) => void;
  checkAuth: () => Promise<void>;
}

// 注册数据接口
interface RegisterData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  phone?: string;
}

// 创建上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 认证提供者组件
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // 登录函数
  const login = async (email: string, password: string): Promise<void> => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      const response = await authAPI.login({ email, password });
      
      if (response.success) {
        dispatch({
          type: 'AUTH_SUCCESS',
          payload: {
            user: response.data.user,
            accessToken: response.data.accessToken,
            refreshToken: response.data.refreshToken,
          },
        });
        message.success('登录成功！');
      } else {
        throw new Error(response.message || '登录失败');
      }
    } catch (error: any) {
      dispatch({ type: 'AUTH_FAILURE' });
      message.error(error.message || '登录失败，请重试');
      throw error;
    }
  };

  // 注册函数
  const register = async (userData: RegisterData): Promise<void> => {
    try {
      dispatch({ type: 'AUTH_START' });
      
      const response = await authAPI.register(userData);
      
      if (response.success) {
        dispatch({
          type: 'AUTH_SUCCESS',
          payload: {
            user: response.data.user,
            accessToken: response.data.accessToken,
            refreshToken: response.data.refreshToken,
          },
        });
        message.success('注册成功！请查收验证邮件');
      } else {
        throw new Error(response.message || '注册失败');
      }
    } catch (error: any) {
      dispatch({ type: 'AUTH_FAILURE' });
      message.error(error.message || '注册失败，请重试');
      throw error;
    }
  };

  // 登出函数
  const logout = async (): Promise<void> => {
    try {
      if (state.accessToken) {
        await authAPI.logout();
      }
    } catch (error) {
      console.error('登出请求失败:', error);
    } finally {
      dispatch({ type: 'LOGOUT' });
      message.success('已安全登出');
    }
  };

  // 刷新访问令牌
  const refreshAccessToken = async (): Promise<void> => {
    try {
      if (!state.refreshToken) {
        throw new Error('没有刷新令牌');
      }

      const response = await authAPI.refreshToken(state.refreshToken);
      
      if (response.success) {
        localStorage.setItem('accessToken', response.data.accessToken);
        localStorage.setItem('refreshToken', response.data.refreshToken);
        
        dispatch({
          type: 'AUTH_SUCCESS',
          payload: {
            user: state.user!,
            accessToken: response.data.accessToken,
            refreshToken: response.data.refreshToken,
          },
        });
      } else {
        throw new Error('刷新令牌失败');
      }
    } catch (error) {
      console.error('刷新令牌失败:', error);
      dispatch({ type: 'AUTH_FAILURE' });
    }
  };

  // 更新用户信息
  const updateUser = (userData: Partial<User>): void => {
    if (state.user) {
      dispatch({
        type: 'UPDATE_USER',
        payload: { ...state.user, ...userData },
      });
    }
  };

  // 检查认证状态
  const checkAuth = async (): Promise<void> => {
    try {
      if (!state.accessToken) {
        dispatch({ type: 'SET_LOADING', payload: false });
        return;
      }

      // 这里可以调用API验证令牌有效性
      // const response = await authAPI.verifyToken();
      // 暂时跳过验证，直接设置为未加载状态
      dispatch({ type: 'SET_LOADING', payload: false });
    } catch (error) {
      console.error('检查认证状态失败:', error);
      dispatch({ type: 'AUTH_FAILURE' });
    }
  };

  // 组件挂载时检查认证状态
  useEffect(() => {
    checkAuth();
  }, []);

  // 设置axios拦截器处理令牌刷新
  useEffect(() => {
    const setupInterceptors = () => {
      // 请求拦截器 - 添加认证头
      const requestInterceptor = authAPI.interceptors.request.use(
        (config) => {
          if (state.accessToken) {
            config.headers.Authorization = `Bearer ${state.accessToken}`;
          }
          return config;
        },
        (error) => Promise.reject(error)
      );

      // 响应拦截器 - 处理令牌过期
      const responseInterceptor = authAPI.interceptors.response.use(
        (response) => response,
        async (error) => {
          const originalRequest = error.config;

          if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
              await refreshAccessToken();
              originalRequest.headers.Authorization = `Bearer ${state.accessToken}`;
              return authAPI(originalRequest);
            } catch (refreshError) {
              dispatch({ type: 'AUTH_FAILURE' });
              return Promise.reject(refreshError);
            }
          }

          return Promise.reject(error);
        }
      );

      return () => {
        authAPI.interceptors.request.eject(requestInterceptor);
        authAPI.interceptors.response.eject(responseInterceptor);
      };
    };

    const cleanup = setupInterceptors();
    return cleanup;
  }, [state.accessToken, state.refreshToken]);

  const contextValue: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshAccessToken,
    updateUser,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// 使用认证上下文的Hook
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth必须在AuthProvider内部使用');
  }
  return context;
};