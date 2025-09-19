```python
  !nvidia-smi
```

```python
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
from sklearn.metrics import mean_squared_error
```

# 导入数据

```python
from google.colab import drive
drive.mount('/content/drive')
```

这次我们准备使用五个监测站的数据。假定Marylebone Road监测站的数据出现异常，此时我们用Bloomsbury, Eltham, Harlington和N_Kensington的数据来推断Marylebone的数据。注意，与之前多变量预测相同，该实验依旧是多变量预测单变量。分多次预测，实现多变量预测多变量。

```python
Marylebone_Road=pd.read_csv('/content/drive/My Drive/air_inference/data/Marylebone_Road_clean.csv')
Bloomsbury=pd.read_csv('/content/drive/My Drive/air_inference/data/Bloomsbury_clean.csv')
Eltham=pd.read_csv('/content/drive/My Drive/air_inference/data/Eltham_clean.csv')
Harlington=pd.read_csv('/content/drive/My Drive/air_inference/data/Harlington_clean.csv')
N_Kensington=pd.read_csv('/content/drive/My Drive/air_inference/data/N_Kensington_clean.csv')
```

```python
Marylebone_Road.head()
```

```python
Marylebone_Road=Marylebone_Road[['nox','no2','no','o3','pm2.5','ws','wd','air_temp']]
Bloomsbury=Bloomsbury[['nox','no2','no','o3','pm2.5','ws','wd','air_temp']]
Eltham=Eltham[['nox','no2','no','o3','pm2.5','ws','wd','air_temp']]
Harlington=Harlington[['nox','no2','no','o3','pm2.5','ws','wd','air_temp']]
N_Kensington=N_Kensington[['nox','no2','no','o3','pm2.5','ws','wd','air_temp']]

```

```python
Marylebone_Road
Bloomsbury
Eltham
Harlington
N_Kensington
```

先将每个监测站的columns更名。加上后缀为监测站的首字母

```python
col_Marylebone=['nox_M','no2_M','no_M','o3_M','pm2.5_M','ws_M','wd_M','air_temp_M']
col_Bloomsbury=['nox_B','no2_B','no_B','o3_B','pm2.5_B','ws_B','wd_B','air_temp_B']
col_Eltham=['nox_E','no2_E','no_E','o3_E','pm2.5_E','ws_E','wd_E','air_temp_E']
col_Harlington=['nox_H','no2_H','no_H','o3_H','pm2.5_H','ws_H','wd_H','air_temp_H']
col_N_Kensington=['nox_N','no2_N','no_N','o3_N','pm2.5_N','ws_N','wd_N','air_temp_N']

Marylebone_Road.columns=col_Marylebone
Bloomsbury.columns=col_Bloomsbury
Eltham.columns=col_Eltham
Harlington.columns=col_Harlington
N_Kensington.columns=col_N_Kensington
```

接下来将所有监测站的数据拼接起来

```python
dataset=Bloomsbury.join(Marylebone_Road)
dataset=dataset.join(Eltham)
dataset=dataset.join(Harlington)
dataset=dataset.join(N_Kensington)
dataset.head()
```

# 多站点多变量进行预测

```python
var_origin=dataset.values
```

数据进行归一化操作

```python
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler(feature_range=(0, 1))
scaled = scaler.fit_transform(var_origin)
```

将数据转为cuda类型

```python
import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
var= torch.FloatTensor(scaled).to(device)
```

划分训练集，验证集和测试集

```python
def splitData(var,per_val,per_test):
    num_val=int(len(var)*per_val)
    num_test=int(len(var)*per_test)
    train_size=int(len(var)-num_val-num_test)
    train_data=var[0:train_size]
    val_data=var[train_size:train_size+num_val]
    test_data=var[train_size+num_val:train_size+num_val+num_test]
    return train_data,val_data,test_data
```

我们的验证集合测试集都取96小时

```python
train_data,val_data,test_data=splitData(var,0.1,0.1)
```

查看长度

```python
print('The length of train data, validation data and test data are:',len(train_data),',',len(val_data),',',len(test_data))
```


取一定大小的窗口进行滑动，每个窗口的label值是窗口下一个预测的第一个空气污染物的值

```python
train_window = 240
def create_train_sequence(input_data, tw):
    inout_seq = []
    L = len(input_data)
    for i in range(L-tw):
        train_seq = input_data[i:i+tw]
        train_label = input_data[i+tw:i+tw+1]
        inout_seq.append((train_seq ,train_label))
    return inout_seq
```

```python
train_inout_seq = create_train_sequence(train_data, train_window)
print('The total number of train windows is',len(train_inout_seq))
```

注意，与上面创建train_data的sequence不同，验证集数据(实验是96个验证集数据)只是label。其数据部分还是需要借助于train集中的数据，大小为一个窗口。而这一个窗口的数据并不会在训练过程中被使用

```python
def create_val_sequence(train_data,val_data, tw):
    temp=torch.cat((train_data,val_data))   #先将训练集和测试集合并
    inout_seq = []
    L = len(val_data)
    for i in range(L):
        val_seq = temp[-(train_window+L)+i:-L+i]
        val_label = test_data[i:i+1]
        inout_seq.append((val_seq ,val_label))

    return inout_seq

val_inout_seq = create_val_sequence(train_data, val_data,train_window)
print('The total number of validation windows is',len(val_inout_seq))
```

 此时的label的shape是[1,40]。注意，真正的label只有这40个值中的前五个

```python
val_inout_seq[0][1].shape
```

```python
def create_test_sequence(train_data,val_data,test_data, tw):
    temp=torch.cat((train_data,val_data))   #先将训练集和测试集合并
    temp=torch.cat((temp,test_data))
    inout_seq = []
    L = len(test_data)
    for i in range(L):
        test_seq = temp[-(train_window+L)+i:-L+i]
        test_label = test_data[i:i+1]
        inout_seq.append((test_seq ,test_label))

    return inout_seq

test_inout_seq = create_test_sequence(train_data, val_data, test_data,train_window)
print('The total number of validation windows is',len(val_inout_seq))
```

# 定义LSTM

这次的数据的维度为40维

```python
train_data.shape
```

```python
from torch import nn
import torch.nn.functional as F
import torch.nn.init as init
import math
class LSTM(nn.Module):
    def __init__(self,input_size=40,hidden_layer_size=50,output_size=1,num_layers=2):
        super().__init__()
        self.hidden_layer_size=hidden_layer_size
        self.lstm=nn.LSTM(input_size,hidden_layer_size,num_layers)
        self.linear1=nn.Linear(hidden_layer_size,hidden_layer_size)
        self.linear2=nn.Linear(hidden_layer_size,output_size)
        self.hidden_cell=(torch.zeros(num_layers,1,self.hidden_layer_size),torch.zeros(num_layers,1,self.hidden_layer_size))
        init_rnn(self.lstm,'xavier')
        
    def forward(self,input_seq):
        lstm_out, self.hidden_cell = self.lstm(input_seq.reshape(len(input_seq),1,40), self.hidden_cell)
        out=self.linear1(lstm_out.view(len(input_seq), -1))
        out=torch.tanh(out)
        predictions = self.linear2(out)
        return predictions[-1]

#设定初始化
def init_rnn(x, type='uniform'):
    for layer in x._all_weights:
        for w in layer:
            if 'weight' in w:
                if type == 'xavier':
                    init.xavier_normal_(getattr(x, w))
                elif type == 'uniform':
                    stdv = 1.0 / math.sqrt(x.hidden_size)
                    init.uniform_(getattr(x, w), -stdv, stdv)
                elif type == 'normal':
                    stdv = 1.0 / math.sqrt(x.hidden_size)
                    init.normal_(getattr(x, w), .0, stdv)
                else:
                    raise ValueError

```

# 训练模型

与之前一样，分别多nox,no2,no,o3和pm2.5进行预测

```python
import copy

epochs=5


#为了实现多变量预测多个单变量，我这里用了五个LSTM模型
model_nox=LSTM().to(device)
model_no2=LSTM().to(device)
model_no=LSTM().to(device)
model_o3=LSTM().to(device)
model_pm25=LSTM().to(device)

loss_function=nn.MSELoss()
optimizer_nox = torch.optim.SGD(model_nox.parameters(), lr=0.003,momentum=0.2)
optimizer_no2 = torch.optim.SGD(model_no2.parameters(), lr=0.002,momentum=0.2, weight_decay=6e-4)
optimizer_no = torch.optim.SGD(model_no.parameters(), lr=0.002,momentum=0.15, weight_decay=6e-4)
optimizer_o3 = torch.optim.SGD(model_o3.parameters(), lr=0.002,momentum=0.2, weight_decay=6e-4)
optimizer_pm25 = torch.optim.SGD(model_pm25.parameters(), lr=0.002,momentum=0.2, weight_decay=6e-4)


attr_dic={
    'nox':model_nox,
    'no2':model_no2,
    'no':model_no,
    'o3':model_o3,
    'pm2.5':model_pm25
}

index_dic={
    'nox':0,
    'no2':1,
    'no':2,
    'o3':3,
    'pm2.5':4
    
}

optimizer_dic={
    'nox':optimizer_nox,
    'no2':optimizer_no2,
    'no':optimizer_no,
    'o3':optimizer_o3,
    'pm2.5':optimizer_pm25
}

loss_train_dic={
    'nox':[],
    'no2':[],
    'no':[],
    'o3':[],
    'pm2.5':[]
}

loss_val_dic={
    'nox':[],
    'no2':[],
    'no':[],
    'o3':[],
    'pm2.5':[]
}

value_train_dic={
    'nox':[],
    'no2':[],
    'no':[],
    'o3':[],
    'pm2.5':[]
}

value_val_dic={
    'nox':[],
    'no2':[],
    'no':[],
    'o3':[],
    'pm2.5':[]
}

```

```python
def train_model(attr,model):
  model.train()
  print('训练',attr,'模型')
  for i in range(epochs):
    #train
    add=0
    for seq,label in train_inout_seq:   
        optimizer_dic[attr].zero_grad()
        seq=seq.to(device)
        label=label.to(device)
        model.hidden_cell = (torch.zeros(2, 1, model.hidden_layer_size).to(device),torch.zeros(2, 1, model.hidden_layer_size).to(device))
        y_pred = model(seq)

        if(i==epochs-1):  #对最后一次epoch的值进行记录
          value_train_dic[attr].append(y_pred)

        single_loss = loss_function(y_pred[0], label[0,index_dic[attr]])   #这里只预测label[attr]的数值，即某个单一的空气污染物
        add+=single_loss
        single_loss .backward()
        optimizer_dic[attr].step()
    loss_train=add/len(train_inout_seq)
    loss_train_dic[attr].append(loss_train)


    #val
    add=0 
    t=0

    val_inputs=train_data[-train_window:]
    fut_pred = len(val_data)

    for seq,label in val_inout_seq:
      with torch.no_grad():
        seq = val_inputs[-train_window:].to(device)
        label=label.to(device)
        y_pred=model(seq)
        single_loss=loss_function(y_pred[0],label[0,index_dic[attr]])  

        add+=single_loss

        if(i==epochs):  #对最后一次epoch的值进行记录
          value_val_dic[attr].append(y_pred)

        #这一步可能比较模糊。首先我们要明确一点的是，y_pred是一个常数。但是我们的val的是nx8维的数。也就是一个
        #数据就有8维。我们对val_inputs的更新实际上是应该更新8维的数。可因为我们是多变量预测单变量，我们每次只是预测一个值
        #所以，解决方法就是，我先把未来的验证集里的8个数添加进去。然后用得出来的值取覆盖相应污染物的值
        temp=copy.deepcopy(val_data[t])
        temp[index_dic[attr]]=y_pred
        temp=temp.view(1,-1)
        
        val_inputs=torch.cat((val_inputs,temp),0)
        t+=0

    loss_val=add/len(val_inout_seq)
    loss_val_dic[attr].append(loss_val)

    print(f'epoch: {i:3}  train_loss:{loss_train:10.8f} val_loss:{loss_val:10.8f}')
  print('----------------------')
```

```python
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error

def test_model(attr,model):
  temp=torch.cat((train_data,val_data))
  test_inputs=temp[-train_window:,:]

  fut_pred = len(test_data)
  test_list=[]
  test_results=copy.deepcopy(test_data)

  model.eval()

  for i in range(fut_pred):
      seq = test_inputs[-train_window:].to(device)
      with torch.no_grad():
          model.hidden = (torch.zeros(1, 1, model.hidden_layer_size),
                          torch.zeros(1, 1, model.hidden_layer_size))
          y_pred=model(seq)
          temp=copy.deepcopy(test_data[i]).view(1,-1)
          # temp[index_dic[attr]]=y_pred
          # temp=temp.view(1,-1)
          test_inputs=torch.cat((test_inputs,temp),0)
          test_results[i]=y_pred




  actual_predictions = scaler.inverse_transform(np.array(test_results.cpu()))




  x = np.arange(len(train_data)+len(val_data), len(dataset), 1)
  plt.figure(figsize=(8, 6))
  plt.grid(True)

  plt.plot(dataset.loc[len(dataset)-len(test_data):,attr+'_B'].values,color="red",label='real value')
  plt.plot(actual_predictions[:,index_dic[attr]],label='prediction')

  plt.title('hours vs '+attr)
  plt.ylabel(attr)
  plt.xlabel('hour')

  plt.legend(loc='upper right',fontsize=15)

  y_true=dataset.loc[len(dataset)-len(test_data):,attr+'_B'].values
  y_pred=actual_predictions[:,index_dic[attr]]
  print('mse: ',mean_squared_error(y_true, y_pred))
  print('mae: ',mean_absolute_error(y_true, y_pred))
```

```python
train_model('nox',model_nox)
```

```python
test_model('nox',model_nox)
```

```python
train_model('no2',model_no2)
```

```python
test_model('no2',model_no2)
```

```python
train_model('no',model_no)
```

```python
test_model('no',model_no)
```

```python
train_model('o3',model_o3)
```

```python
test_model('o3',model_o3)
```

```python
test_model('o3',model_o3)
```

```python
train_model('pm2.5',model_pm25)
```

```python
test_model('pm2.5',model_pm25)
```

# 预测未来24小时的数据

```python
def predict_future(attr,model):
  temp=torch.cat((train_data,val_data))
  test_inputs=temp[-train_window:,:]

  fut_pred = 96
  test_list=[]
  test_results=copy.deepcopy(test_data)

  model.eval()

  for i in range(fut_pred):
      seq = test_inputs[-train_window:].to(device)
      with torch.no_grad():
          model.hidden = (torch.zeros(1, 1, model.hidden_layer_size),
                          torch.zeros(1, 1, model.hidden_layer_size))
          y_pred=model(seq)
          temp=copy.deepcopy(test_data[i])
          temp[index_dic[attr]]=y_pred
          temp=temp.view(1,-1)
          test_inputs=torch.cat((test_inputs,temp),0)
          test_results[i]=y_pred




  actual_predictions = scaler.inverse_transform(np.array(test_results.cpu()))





  plt.figure(figsize=(8, 6))
  plt.grid(True)

  plt.plot(dataset.loc[len(dataset)-len(test_data):len(dataset)-len(test_data)+fut_pred,attr+'_B'].values,color="red",label='real value')
  plt.plot(actual_predictions[:fut_pred,index_dic[attr]],label='prediction')

  plt.title('hours vs '+attr)
  plt.ylabel(attr)
  plt.xlabel('hour')

  plt.legend(loc='upper right',fontsize=15)

  y_true=dataset.loc[len(dataset)-len(test_data):len(dataset)-len(test_data)+fut_pred-1,attr+'_B'].values
  y_pred=actual_predictions[:fut_pred,index_dic[attr]]

  print('mse: ',mean_squared_error(y_true, y_pred))
  print('mae: ',mean_absolute_error(y_true, y_pred))

  y_pred=pd.DataFrame(y_pred)

  y_pred.to_csv('/content/drive/My Drive/air_inference/result24/lstm_mul_sites'+attr+'.csv',index=False)
```

```python
predict_future('nox',model_nox)
```

```python
predict_future('no2',model_no2)
```

```python
predict_future('no',model_no)
```

```python
predict_future('o3',model_o3)
```

```python
predict_future('pm2.5',model_pm25)
```