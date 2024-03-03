real_msg_channel  = [0,2,1,0,1]
chunks = 5
l = 0
r = 4
msg = "abcdefgklmnopqs485asdf6489"
for i in range(chunks):
    encoded_msg = msg[l:r]
    messages = [0] * 3;
    channels = [0] * 3;
    l += 4
    r += 4
    messages[real_msg_channel[i]] = encoded_msg;
    channels[real_msg_channel[i]] = 'R';
    for j in range(3): 
        if j == real_msg_channel[i]: continue
        messages[j] = encoded_msg
        channels[j] = 'E';
    print(messages)
    print(f"{channels}")
