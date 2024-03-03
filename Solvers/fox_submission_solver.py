import requests
import numpy as np
from riddle_solvers import *

api_base_url = "http://3.70.97.142:5000"
team_id = "kNgGFJe"
msg = ""
current_fake = 0


class LSBSteg:
    def __init__(self, im):
        self.image = im
        self.height, self.width, self.nbchannels = im.shape
        self.size = self.width * self.height

        self.maskONEValues = [1, 2, 4, 8, 16, 32, 64, 128]
        # Mask used to put one ex:1->00000001, 2->00000010 .. associated with OR bitwise
        self.maskONE = self.maskONEValues.pop(
            0
        )  # Will be used to do bitwise operations

        self.maskZEROValues = [254, 253, 251, 247, 239, 223, 191, 127]
        # Mak used to put zero ex:254->11111110, 253->11111101 .. associated with AND bitwise
        self.maskZERO = self.maskZEROValues.pop(0)

        self.curwidth = 0  # Current width position
        self.curheight = 0  # Current height position
        self.curchan = 0  # Current channel position

    def put_binary_value(self, bits):  # Put the bits in the image
        for c in bits:
            val = list(
                self.image[self.curheight, self.curwidth]
            )  # Get the pixel value as a list
            if int(c) == 1:
                val[self.curchan] = (
                    int(val[self.curchan]) | self.maskONE
                )  # OR with maskONE
            else:
                val[self.curchan] = (
                    int(val[self.curchan]) & self.maskZERO
                )  # AND with maskZERO

            self.image[self.curheight, self.curwidth] = tuple(val)
            self.next_slot()  # Move "cursor" to the next space

    def next_slot(self):  # Move to the next slot were information can be taken or put
        if self.curchan == self.nbchannels - 1:  # Next Space is the following channel
            self.curchan = 0
            if (
                self.curwidth == self.width - 1
            ):  # Or the first channel of the next pixel of the same line
                self.curwidth = 0
                if (
                    self.curheight == self.height - 1
                ):  # Or the first channel of the first pixel of the next line
                    self.curheight = 0
                    if self.maskONE == 128:  # Mask 1000000, so the last mask
                        raise SteganographyException(
                            "No available slot remaining (image filled)"
                        )
                    else:  # Or instead of using the first bit start using the second and so on..
                        self.maskONE = self.maskONEValues.pop(0)
                        self.maskZERO = self.maskZEROValues.pop(0)
                else:
                    self.curheight += 1
            else:
                self.curwidth += 1
        else:
            self.curchan += 1

    def read_bit(self):  # Read a single bit int the image
        val = self.image[self.curheight, self.curwidth][self.curchan]
        val = int(val) & self.maskONE
        self.next_slot()
        if val > 0:
            return "1"
        else:
            return "0"

    def read_byte(self):
        return self.read_bits(8)

    def read_bits(self, nb):  # Read the given number of bits
        bits = ""
        for i in range(nb):
            bits += self.read_bit()
        return bits

    def byteValue(self, val):
        return self.binary_value(val, 8)

    def binary_value(self, val, bitsize):  # Return the binary value of an int as a byte
        binval = bin(val)[2:]
        if len(binval) > bitsize:
            raise SteganographyException("binary value larger than the expected size")
        while len(binval) < bitsize:
            binval = "0" + binval
        return binval

    def encode_text(self, txt):
        l = len(txt)
        binl = self.binary_value(
            l, 16
        )  # Length coded on 2 bytes so the text size can be up to 65536 bytes long
        self.put_binary_value(binl)  # Put text length coded on 4 bytes
        for char in txt:  # And put all the chars
            c = ord(char)
            self.put_binary_value(self.byteValue(c))
        return self.image

    def decode_text(self):
        ls = self.read_bits(16)  # Read the text size in bytes
        l = int(ls, 2)
        i = 0
        unhideTxt = ""
        while i < l:  # Read all bytes of the text
            tmp = self.read_byte()  # So one byte
            i += 1
            unhideTxt += chr(int(tmp, 2))  # Every chars concatenated to str
        return unhideTxt

    def encode_image(self, imtohide):
        w = imtohide.width
        h = imtohide.height
        if self.width * self.height * self.nbchannels < w * h * imtohide.channels:
            raise SteganographyException(
                "Carrier image not big enough to hold all the datas to steganography"
            )
        binw = self.binary_value(w, 16)  # Width coded on to byte so width up to 65536
        binh = self.binary_value(h, 16)
        self.put_binary_value(binw)  # Put width
        self.put_binary_value(binh)  # Put height
        for h in range(
            imtohide.height
        ):  # Iterate the hole image to put every pixel values
            for w in range(imtohide.width):
                for chan in range(imtohide.channels):
                    val = imtohide[h, w][chan]
                    self.put_binary_value(self.byteValue(int(val)))
        return self.image

    def decode_image(self):
        width = int(self.read_bits(16), 2)  # Read 16bits and convert it in int
        height = int(self.read_bits(16), 2)
        unhideimg = np.zeros(
            (width, height, 3), np.uint8
        )  # Create an image in which we will put all the pixels read
        for h in range(height):
            for w in range(width):
                for chan in range(unhideimg.channels):
                    val = list(unhideimg[h, w])
                    val[chan] = int(self.read_byte(), 2)  # Read the value
                    unhideimg[h, w] = tuple(val)
        return unhideimg

    def encode_binary(self, data):
        l = len(data)
        if self.width * self.height * self.nbchannels < l + 64:
            raise SteganographyException(
                "Carrier image not big enough to hold all the datas to steganography"
            )
        self.put_binary_value(self.binary_value(l, 64))
        for byte in data:
            byte = byte if isinstance(byte, int) else ord(byte)  # Compat py2/py3
            self.put_binary_value(self.byteValue(byte))
        return self.image

    def decode_binary(self):
        l = int(self.read_bits(64), 2)
        output = b""
        for i in range(l):
            output += chr(int(self.read_byte(), 2)).encode("utf-8")
        return output


def encode(image: np.ndarray, message: str) -> np.array:
    # steg = LSBSteg(cv2.imread(filepath))
    steg = LSBSteg(image)
    img_encoded = steg.encode_text(message)
    return img_encoded


def init_fox(team_id):
    """
    In this function you need to hit to the endpoint to start the game as a fox with your team id.
    If a sucessful response is returned, you will recive back the message that you can break into chunkcs
    and the carrier image that you will encode the chunk in it.
    """
    response = requests.post(api_base_url + "/fox/start", json={"teamId": team_id})
    response_data = response.json()
    msg = response_data["msg"]
    print(f"Message: {msg}")
    return response_data["carrier_image"]


def solving_problems():
    test_case = get_riddle(team_id, "problem_solving_easy")
    sol = solve_problem_solving_easy(test_case)
    if solve_riddle(team_id, sol):
        current_fake += 1
    test_case = get_riddle(team_id, "problem_solving_medium")
    sol = solve_problem_solving_medium(test_case)
    if solve_riddle(team_id, sol):
        current_fake += 2
    test_case = get_riddle(team_id, "problem_solving_hard")
    sol = solve_problem_solving_hard(test_case)
    if solve_riddle(team_id, sol):
        current_fake += 3
    test_case = get_riddle(team_id, "sec_medium_stegano")
    sol = solve_sec_medium(test_case)
    if solve_riddle(team_id, sol):
        current_fake += 2


# generate one chunk
def generate_message_array(message, image_carrier) -> np.array:
    """
    In this function you will need to create your own startegy. That includes:
        1. How you are going to split the real message into chunks
        2. Include any fake chunks
        3. Decide what 3 chunks you will send in each turn in the 3 channels & what is their entities (F,R,E)
        4. Encode each chunk in the image carrier
    """
    encoded_np_image = encode(image_carrier, message)
    return encoded_np_image


def get_riddle(team_id, riddle_id):
    """
    In this function you will hit the api end point that requests the type of riddle you want to solve.
    use the riddle id to request the specific riddle.
    Note that:
        1. Once you requested a riddle you cannot request it again per game.
        2. Each riddle has a timeout if you didnot reply with your answer it will be considered as a wrong answer.
        3. You cannot request several riddles at a time, so requesting a new riddle without answering the old one
          will allow you to answer only the new riddle and you will have no access again to the old riddle.
    """
    response = requests.post(
        api_base_url + "/fox/get-riddle",
        json={"teamId": team_id, "riddleId": riddle_id},
    )
    response_data = response.json()
    return response_data["test_case"]


def solve_riddle(team_id, solution):
    """
    In this function you will solve the riddle that you have requested.
    You will hit the API end point that submits your answer.
    Use te riddle_solvers.py to implement the logic of each riddle.
    """
    response = requests.post(
        api_base_url + "/fox/solve-riddle",
        json={"teamId": team_id, "solution": solution},
    )
    response_data = response.json()
    print(f"solve_riddle: [budget increase: {response_data}")
    if response_data["status"] == "success":
        return True
    else:
        return False


def send_message(
    team_id, messages, message_entities
):  #  messages must be np.array  =["F", "E", "R"]
    """
    Use this function to call the api end point to send one chunk of the message.
    You will need to send the message (images) in each of the 3 channels along with their entites.
    Refer to the API documentation to know more about what needs to be send in this api call.
    """
    messages[0] = messages[0].tolist()
    messages[1] = messages[1].tolist()
    messages[2] = messages[2].tolist()
    response = requests.post(
        api_base_url + "/fox/send-message",
        json={
            "teamId": team_id,
            "messages": messages,
            "message_entities": message_entities,
        },
    )
    res_data = response.json()
    print(f"send_message: {res_data}")


def end_fox(team_id):
    """
    Use this function to call the api end point of ending the fox game.
    Note that:
    1. Not calling this function will cost you in the scoring function
    2. Calling it without sending all the real messages will also affect your scoring fucntion
      (Like failing to submit the entire message within the timelimit of the game).
    """
    response = requests.post(api_base_url + "/fox/end-game", json={"teamId": team_id})
    res_data = response.json()
    print(f"end_fox: {res_data}")


def submit_fox_attempt(team_id):
    """
    Call this function to start playing as a fox.
    You should submit with your own team id that was sent to you in the email.
    Remeber you have up to 15 Submissions as a Fox In phase1.
    In this function you should:
        1. Initialize the game as fox
        2. Solve riddles
        3. Make your own Strategy of sending the messages in the 3 channels
        4. Make your own Strategy of splitting the message into chunks
        5. Send the messages
        6. End the Game
    Note that:
        1. You HAVE to start and end the game on your own. The time between the starting and ending the game is taken into the scoring function
        2. You can send in the 3 channels any combination of F(Fake),R(Real),E(Empty) under the conditions that
            2.a. At most one real message is sent
            2.b. You cannot send 3 E(Empty) messages, there should be atleast R(Real)/F(Fake)
        3. Refer To the documentation to know more about the API handling
    """
    carrier_image = init_fox(team_id)
    solving_problems()
    real_msg_channel = [0, 2, 1, 0, 1]
    chunks = 5
    l, r = 0, 4
    for i in range(chunks):
        encoded_msg = generate_message_array(
            message=msg[l:r], image_carrier=carrier_image
        )
        messages = [0] * 3
        channels = [0] * 3
        l += 4
        r += 4
        messages[real_msg_channel[i]] = encoded_msg
        channels[real_msg_channel[i]] = "R"
        for j in range(3):
            if j == real_msg_channel[i]:
                continue
            messages[j] = carrier_image
            channels[j] = "E"
        send_message(team_id, messages=messages, message_entities=channels)
    end_fox(team_id)


submit_fox_attempt(team_id)
