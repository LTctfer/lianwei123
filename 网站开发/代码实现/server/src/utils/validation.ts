import Joi from 'joi';
import { Request, Response, NextFunction } from 'express';
import { CustomError } from '../middleware/errorHandler';

// 通用验证中间件
export const validate = (schema: Joi.ObjectSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const { error } = schema.validate(req.body, { abortEarly: false });
    
    if (error) {
      const errorMessage = error.details
        .map(detail => detail.message)
        .join(', ');
      
      throw new CustomError(errorMessage, 400);
    }
    
    next();
  };
};

// 用户注册验证
export const registerSchema = Joi.object({
  username: Joi.string()
    .alphanum()
    .min(3)
    .max(20)
    .required()
    .messages({
      'string.alphanum': '用户名只能包含字母和数字',
      'string.min': '用户名至少3个字符',
      'string.max': '用户名最多20个字符',
      'any.required': '用户名是必填项'
    }),
  
  email: Joi.string()
    .email()
    .required()
    .messages({
      'string.email': '请输入有效的邮箱地址',
      'any.required': '邮箱是必填项'
    }),
  
  password: Joi.string()
    .min(8)
    .max(20)
    .pattern(new RegExp('^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)'))
    .required()
    .messages({
      'string.min': '密码至少8个字符',
      'string.max': '密码最多20个字符',
      'string.pattern.base': '密码必须包含大小写字母和数字',
      'any.required': '密码是必填项'
    }),
  
  confirmPassword: Joi.string()
    .valid(Joi.ref('password'))
    .required()
    .messages({
      'any.only': '确认密码与密码不匹配',
      'any.required': '确认密码是必填项'
    }),
  
  phone: Joi.string()
    .pattern(new RegExp('^1[3-9]\\d{9}$'))
    .messages({
      'string.pattern.base': '请输入有效的手机号码'
    })
});

// 用户登录验证
export const loginSchema = Joi.object({
  email: Joi.string()
    .email()
    .required()
    .messages({
      'string.email': '请输入有效的邮箱地址',
      'any.required': '邮箱是必填项'
    }),
  
  password: Joi.string()
    .required()
    .messages({
      'any.required': '密码是必填项'
    })
});

// 产品创建验证
export const productSchema = Joi.object({
  name: Joi.string()
    .min(1)
    .max(255)
    .required()
    .messages({
      'string.min': '产品名称不能为空',
      'string.max': '产品名称最多255个字符',
      'any.required': '产品名称是必填项'
    }),
  
  description: Joi.string()
    .max(1000)
    .messages({
      'string.max': '产品描述最多1000个字符'
    }),
  
  price: Joi.number()
    .positive()
    .precision(2)
    .required()
    .messages({
      'number.positive': '价格必须大于0',
      'any.required': '价格是必填项'
    }),
  
  stock: Joi.number()
    .integer()
    .min(0)
    .required()
    .messages({
      'number.integer': '库存必须是整数',
      'number.min': '库存不能小于0',
      'any.required': '库存是必填项'
    }),
  
  categoryId: Joi.number()
    .integer()
    .positive()
    .required()
    .messages({
      'number.integer': '分类ID必须是整数',
      'number.positive': '分类ID必须大于0',
      'any.required': '分类是必填项'
    }),
  
  tags: Joi.string()
    .max(500)
    .messages({
      'string.max': '标签最多500个字符'
    })
});

// 订单创建验证
export const orderSchema = Joi.object({
  items: Joi.array()
    .items(
      Joi.object({
        productId: Joi.number().integer().positive().required(),
        quantity: Joi.number().integer().positive().required()
      })
    )
    .min(1)
    .required()
    .messages({
      'array.min': '订单至少包含一个商品',
      'any.required': '商品列表是必填项'
    }),
  
  addressId: Joi.number()
    .integer()
    .positive()
    .required()
    .messages({
      'number.integer': '地址ID必须是整数',
      'number.positive': '地址ID必须大于0',
      'any.required': '收货地址是必填项'
    }),
  
  paymentMethod: Joi.string()
    .valid('alipay', 'wechat', 'card')
    .required()
    .messages({
      'any.only': '支付方式必须是alipay、wechat或card之一',
      'any.required': '支付方式是必填项'
    })
});

// 评论创建验证
export const commentSchema = Joi.object({
  content: Joi.string()
    .min(1)
    .max(1000)
    .required()
    .messages({
      'string.min': '评论内容不能为空',
      'string.max': '评论内容最多1000个字符',
      'any.required': '评论内容是必填项'
    }),
  
  rating: Joi.number()
    .integer()
    .min(1)
    .max(5)
    .messages({
      'number.integer': '评分必须是整数',
      'number.min': '评分最低1分',
      'number.max': '评分最高5分'
    }),
  
  productId: Joi.number()
    .integer()
    .positive()
    .messages({
      'number.integer': '产品ID必须是整数',
      'number.positive': '产品ID必须大于0'
    }),
  
  postId: Joi.number()
    .integer()
    .positive()
    .messages({
      'number.integer': '帖子ID必须是整数',
      'number.positive': '帖子ID必须大于0'
    }),
  
  parentId: Joi.number()
    .integer()
    .positive()
    .messages({
      'number.integer': '父评论ID必须是整数',
      'number.positive': '父评论ID必须大于0'
    })
});

// 文章创建验证
export const postSchema = Joi.object({
  title: Joi.string()
    .min(1)
    .max(255)
    .required()
    .messages({
      'string.min': '文章标题不能为空',
      'string.max': '文章标题最多255个字符',
      'any.required': '文章标题是必填项'
    }),
  
  content: Joi.string()
    .min(1)
    .required()
    .messages({
      'string.min': '文章内容不能为空',
      'any.required': '文章内容是必填项'
    }),
  
  excerpt: Joi.string()
    .max(500)
    .messages({
      'string.max': '文章摘要最多500个字符'
    }),
  
  categoryId: Joi.number()
    .integer()
    .positive()
    .messages({
      'number.integer': '分类ID必须是整数',
      'number.positive': '分类ID必须大于0'
    }),
  
  tags: Joi.string()
    .max(500)
    .messages({
      'string.max': '标签最多500个字符'
    }),
  
  status: Joi.string()
    .valid('DRAFT', 'PUBLISHED', 'ARCHIVED')
    .default('DRAFT')
    .messages({
      'any.only': '状态必须是DRAFT、PUBLISHED或ARCHIVED之一'
    })
});

// 分页验证
export const paginationSchema = Joi.object({
  page: Joi.number()
    .integer()
    .min(1)
    .default(1)
    .messages({
      'number.integer': '页码必须是整数',
      'number.min': '页码最小为1'
    }),
  
  limit: Joi.number()
    .integer()
    .min(1)
    .max(100)
    .default(10)
    .messages({
      'number.integer': '每页数量必须是整数',
      'number.min': '每页数量最小为1',
      'number.max': '每页数量最大为100'
    })
});

// ID参数验证
export const idSchema = Joi.object({
  id: Joi.number()
    .integer()
    .positive()
    .required()
    .messages({
      'number.integer': 'ID必须是整数',
      'number.positive': 'ID必须大于0',
      'any.required': 'ID是必填项'
    })
});