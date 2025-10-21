viết extension để đọc vào  https://messenger.refinitiv.com/messenger/ 
gửi hết các dữ liệu trên trang web về server kafka ở local

như vậy phải viết 1 service kafka
và 1 extension liên tục đọc và tracking trong trang web đấy.


hãy tạo ra theo đúng thứ tự từ phân tích bài toán đến đưa ra phương án
rồi mới code 

sample_data 
đây là folder chưa html của trang web được download bằng tay thủ công để tham khảo 

tạo ra các file phân tích yêu cầu và mô tả kiến trúc giải pháp 

khong viết kafka nữa
viết 1 api đơn giản thông thường thôi 


như này có hoạt động đúng k?

tự mình chat thì không có dữ liệu à?

no extract anything
giải thích từng bước trong quá trình extract

thử viết riêng 1 đoạn script để chạy trong console của trình duyệt 
để extract được lịch sử chat trước

https://messenger.refinitiv.com/messenger/

[12:49:41] Bạn: Hi
[12:50:05] Bạn: Anh Dũng , chat thử với em
[13:37:18] Bạn: 2
[14:36:29] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: hihi anh
[09:20:45] Bạn: alo
[09:21:03] Bạn: Quân nhận được MSG của anh ko?
[09:21:14] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: co anh a
[09:21:30] Bạn: ok done vậy là ổn để bàn giao bên CN
[09:21:44] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: vang
[09:35:35] Bạn: A cần vào cái room có các dealer giao dịch để thu thập lịch sử dữ liệu thật
[09:36:54] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: room đấy phải đăng ký mới vào được anh
[09:37:02] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: ko phải trader ko vào được
[09:57:03] Bạn: thế đk thêm cho IT có được
[09:57:03] Bạn: ok
[10:06:51] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: user IT thì anh check về hệ thống thôi, còn muốn lấy dữ liệu vẫn cần dùng user của trader anh a
[10:06:58] Bạn: uh
[10:07:07] Bạn: ý A là đk thêm 1 trader cho con AI boot
[10:16:09] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: anh cần cài đặt gì cài đặt lên máy của trader trên này anh a
[10:16:25] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: giờ đăng ký user vào room cũng phải xác thực
[10:40:31] Bạn: ko
[10:40:42] Bạn: A khảo sát cái test room này
[10:40:52] Bạn: thì nó ko có lưu log chat xuống máy trạm
[10:41:21] Bạn: pá tiếp theo là quay phim màn hình của trader
[10:41:40] Bạn: thì sẽ vướng việc trader cũng ko giữ ổn định màn hình chat liên tục
[10:41:52] Bạn: sẽ switch sang màn hình khác
[10:42:09] Bạn: kéo lên xuống màn hình chat để xem lại đoạn trước
[10:42:20] Bạn: => Cũng ko ra được kết quả chính xác
[10:42:53] Bạn: nên tốt nhất vẫn phải là có 1 user để login, tàu ngầm theo dõi rooom liên tục trên 1 máy trạm độc lập
[10:43:19] Bạn: nên sẽ cần 1 user riêng cho con boot AI này dùng
[10:43:38] Bạn: nó sẽ chỉ theo dõi, ko chat gì, ko kéo lên kéo xuống, ko quay đi chỗ khác
[10:44:04] Bạn: E cú coi như MSB có thêm 1 trader mới
[10:44:12] Bạn: đk user mới thôi
[10:44:22] Bạn: có phát sinh chi phí hay vướng thủ tục gì ko
[17:20:25] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: có anh ah, hiện tại để vào room thì phải có xác nhận
[17:20:40] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: bọn em ko tự mở ra user ảo để đưa vào room được
[17:20:54] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: có thể cài trên máy em, hay máy các bạn khác
[17:21:04] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: đảm bảo có login và đăng nhập vào room
[17:21:10] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: nhưng anh thử tính p/á
[17:21:25] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: bọn em cũng ko thể để im một cái màn hình đó suốt được
[17:21:30] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: phải chuyển đổi màn hình
[17:21:37] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: làm việc khác
[17:21:48] Quan Nguyen Hai - Vietnam Maritime Commercial Joint Stock Bank: mà hệ thống vẫn tự động lấy được dữ liệu của room ko ?
[18:20:45] Bạn: em xin phép test nhiều tin nhắn liên tục ạ.
Các anh mute room này giúp em nhé ạ
[18:34:34] Bạn: a
[18:34:53] Bạn: a
[18:38:02] Bạn: a
[18:38:36] Bạn: a
[19:04:34] Bạn: 7h rồi


viết 1 extension khác thật đơn giản ngắn gọn , tối thiểu code có thể
gửi mail đến server nội bộ 
aiplatform@msb.com.vn
pass: Zxcv@1234

gửi mail đến trongnq5@msb.com.vn

để extension mới trong 1 folder riêng

how to show log bug?

phân tích bài toán này có khả thi hay không? để gửi mail trực tiếp từ extension 
có cách nào pypass hay không?


đây là code extract chuẩn nhất 
hãy update vào code base để extract đúng theo như này