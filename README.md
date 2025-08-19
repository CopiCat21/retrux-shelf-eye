# retrux-shelf-components

# Setup Python

```
# python 3.11.12

$ pyenv install 3.11.12
$ pyenv virtualenv 3.11.12 product-scanner
$ pyenv activate product-scanner
$ python -m pip install -r requirements.txt
```

# Setup Directories

```
# Setup "/Users/retruxosaproject" (MacOS Mengunakan Uppercase U)

$ sudo mkdir -p /Users/retruxosaproject
$ sudo chown $(id -u):$(id -g) -R /Users/retruxosaproject
$ mkdir -p /Users/retruxosaproject/app_root/active_state
```


# Setup System

## 1. Setup Camera
Jalankan Kamera Server dulu (jangan di stop sampai selesai karena bisa akan reset)

```
/Users/retruxosaproject/.pyenv/versions/camscan_env/bin/python /Users/retruxosaproject/app_root/binaries/cam_service/camera_server.py
```

## 2. Setup Shelf Scanner

```
/Users/retruxosaproject/app_root/binaries/product_scan/shelf_scanner.zsh setup
```

## 3. Configure Metadata Product
Letak product nama akan ada di 

```
/Users/retruxosaproject/app_root/active_state/product_information/*.json
```

modifikasi nama product, format bounding box 'coords' adalah xyxy dengan tipe data list[int]

## 4. Running Service

Jalankan Service Shelf Scanner di background
```
/Users/retruxosaproject/app_root/binaries/product_scan/shelf_scanner.zsh service
```

File file akan ter-update automatic termasuk dengan scheduler supaya tidak crash atau lag system. 

# Setup Updated System

## 1. Pastikan path dan venv sudah benar

contoh path yang benar
````
(venv) PS E:\Projects\retrux-shelf-components-main>
````
pastikan juga venv juga sudah aktif

## 2. Jalankan UI

jalankan UI dengan command berikut
````
python .\cam_service\gui_camera_server.py
````

## 3. Camera Server (Continously Running)

Pilih input device dari camera atau gambar (seharusnya belum bisa video)
Klik start untuk mulai. proses ini akan jalan terus menerus

## 4. Shelf Setup (One Time)

Klik Run Shelf Setup untuk memulai setup.
Tunggu sampai proses selesai.

## 5. Shelf Service (Contiously Running)

Proses ini jalan terus menerus

## 6. Display Image

Dapat memilih gambar sebelum dan setelah deteksi.