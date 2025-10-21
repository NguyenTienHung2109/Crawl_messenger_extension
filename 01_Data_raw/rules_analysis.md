# Document Analysis: Rule-FX-Message.docx

**Source File:** `D:\Projects\03.FI_crawldata\01_Data_raw\Rule-FX-Message.docx`

## Rule FX Message

- Sau khi kéo được data về dữ liệu dưới dạng excel bao gồm thời gian, mail và text.
- Dữ liệu được format theo dạng sau
- Dữ liệu được trả về sẽ được xử lý như sau:
- Note: A = trader Start, B = trader reply, X = text
## Quy trình xử lý

## Các câu lệnh “Start”

- Định nghĩa Start:
- Cách 1: thỏa mãn 3 bước 1,2,3
- Bước 1: Scan X for number ( số nguyên)
- If wrong, not a “Start”
- Bước 2: Scan X for “bid”, “ask”, “offer”, “off”, “bán”, “mua”, “có”, “còn”
- If wrong, Not a “Start”
- If right, “bid”, “mua” = bid, “ask”, “offer”, “off”, “có”, “còn” = offer
- Bước 3: Scan X for “on”, “spt”, “1m”, “1w”, “spot”, “6m”, “3m”, “2m”, “6w”,  số âm
- If right, Not a “Start”
- Bước 4: Scan for “for”, “u”, “k”, “mio” . Yếu tố option bổ sung giúp đầy đủ nội dung của câu Start
- If wrong, scan number = price
- If catch “for”, scan number before “for” = price (Nếu 2 số = bid – ask, 1 số  xét theo bid-ask, number after “for” = volume)
- If catch “u”, “mio”, “k” the preceding number = volume, the other number = price
- Cách 2: Scan for Only 2 numbers, No1/ No2, No1 – No2, No1/No2 for No3, No1*No2
- If right, Bid = number 1, ask = number 2
- If 1 Number, check xem liệu trader này có quote 1 lệnh Reply ngay bên trên (trong vòng 30s) hay ko
- Ouput example:
- Trong trường hợp các trường bid, ask và volume ko đầy đủ, bỏ trống data dạng Null
- Ví dụ các trường hợp phổ biến:
- Cách 2 => bid 41, offer 45
- Cách 1: Có số, có “offer” => offer 45
- Không phải Start. Câu lệnh “41” thuộc về câu đầy đủ : “buy Minh 10u 41” của anh Thái.
- Không phải Start. Dù có bid, có số nhưng không nguyên
- Start. Có offer, có 45. Scan bước 4 => amount = 500k (0.5 mio ~ 0.5u)
- Start. => Offer giá 50 với khối lượng là 10u (10 triệu usd)
- Start. “bán”
## Các câu lệnh “Reply”

- Bước 1: Scan “buy”, “sell”, “khớp” from other trader
- If wrong, ignored
- If right, position được xác định buy = B buy, A sell và ngược lại
- Bước 2: Scan “u”
- If right, the preceding number = vol of B
- Sau khi lệnh Reply của B được phát hiện, lệnh này đồng thời trở thành 1 lệnh Start mới của B và được tiếp tục xử lý theo quy trình cũ
- Ouput example:
- Ví dụ:
- Để dễ hình dung, giả sử đây là lệnh Reply cho lệnh Start của Minh. Minh Start: Offer 30
- VPBank buy
- Volume: 5u, key calling: Minh
- Đồng thời, lệnh Reply này được xét như là một lệnh Start mới: Tuấn bid 30.
- Các anh xem xét ví dụ sau
- Huy start: Offer 44
- Tìm lệnh confirm của Huy => “done Thái 6u nhé”
- Lọc từ 9:51:16 đến 9:52:02. Tìm lệnh Reply trong khoảng này
- Lệnh Reply từ Thái: buy a Huy
- Ngoài ra, trong khoảng tgian này Thái còn nhắn “10u” => Thái buy a Huy 10u
- Lệnh Reply của Thái đồng nghĩa 1 lệnh Start mới: Thái bid 44
- Khi lệnh này được coi là 1 lệnh Start. Tiếp tục tìm lệnh confirm của Thái => “oki anh Nhân anh Quảng”
- Lọc tìm lệnh reply từ 9:51:53 đến 9:52:20
- Lại tiếp tục quy trình như bình thường.
## Các câu lệnh “Confirm”

- Bước 1: Scan “done”, “ok”, “not suit”, from A
- If wrong, ignore
- Nếu có 2 câu lệnh Confirm trở lên, scan từ câu muộn nhất của A về trước, ignore all below.
- If “not suit
- Bước 2: Scan “u”
- If right, the preceding number = vol of A
- Bước 3: Scan B & A
- From Key Calling of B, scan any relevant in “confirm” of A
- From Key Calling of A, scan any relevant in “reply” of B
- Double check: Scan for reconfirm from B to assure the deal (to increase the confident)
- Từ lệnh confirm của A, scan “tks” from B trong 2 phút từ lệnh confirm của A. If right, increase the probability = 100%
- Bước 4: Chốt deal
- From side of A and B => side of Bank
- From volume which lower from A and B => volume of the deal
- Nếu chỉ ghi nhận được 1 giá trị volume từ hoặc A or B => ghi volume đó = volume của deal
- Match side of B to price of A => price of the deal
## Rule of price: Bắt giá UV tự động mỗi 5 phút

- If 00 <= price <= 99        => Match 2 số cuối với giá UV real time
- If …
- Ouput example:

