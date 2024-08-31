import pyaudio
import numpy as np

class PhysicalLayer:

    #intializing the parameters of the class for creating signals
    def __init__(self,sample_rate,duration,f0,f1,amplitute):
        
        self.sample_rate = sample_rate
        self.duration = duration
        self.f0 = f0
        self.f1 = f1
        self.amplitude = amplitute

        #intializing port
        self.port = pyaudio.PyAudio()
        self.stream = self.port.open(format=pyaudio.paFloat32,
                                    channels=1,
                                    rate=self.sample_rate,
                                    output=True,
                                    input=True
                                    )

    def __del__(self):
        self.stream.stop_stream()
        self.stream.close()
        self.port.terminate()

    def generate_signal(self,bit):

        frequency = 800 if (bit == 1) else 400

        #creating a array of times where we sample audio data
        time_arr = np.linspace(0, self.duration, int(self.duration*self.sample_rate),endpoint=False) 
        signal = self.amplitude*np.sin( 2*np.pi*frequency*time_arr)
        return signal
    
    def transmit(self,bits):
        
        for bit in bits:
            signal = self.generate_signal(bit)
            self.stream.write(signal.astype(np.float32).tobytes())


    def read_signal(self):
        numSamples = int(int(self.sample_rate*self.duration))
        
        rawData = self.stream.read(numSamples)
        signal = np.frombuffer(rawData,dtype = np.float32)
        bit = self.decode_signal(signal)
        return bit


    def decode_signal(self, signal):

        # Decoding logic to convert signal to bit
        # Compute the FFT of the signal to determine the frequency

        frequency_array = []
        num_chunks = 10


        chunk_size = int(len(signal)/num_chunks)
        
        for i in range( 0,int(self.duration*self.sample_rate) ,int(chunk_size)):
            
            signal_chunk = signal[i : i+chunk_size]
            fft_values = np.fft.fft(signal_chunk)

            frequencies = np.fft.fftfreq(len(signal_chunk),d=1/self.sample_rate)

            dominant_frequency = abs(frequencies[np.argmax(np.abs(fft_values))])
            frequency_array.append(dominant_frequency)

        firstHalfSum = 0
        secondHalfSum = 0

        for frequency in frequency_array[0:5]:
            bit = 1 if abs(frequency - self.f1) < abs(frequency - self.f0) else 0
            firstHalfSum += bit
        for frequency in frequency_array[5:10]:
            bit = 1 if abs(frequency - self.f1) < abs(frequency - self.f0) else 0
            secondHalfSum += bit
        
        sum = firstHalfSum+secondHalfSum
        
        if sum>5:
            return 1
        if sum < 5:
            return 0
        if secondHalfSum < 2.5 :
            return 0
        else :
            return 1


class DLL:

    def __init__(self,physical_layer):
        self.physical_layer = physical_layer

    def decrypt(self,data):
        return data
    
    def recieve(self):

        recived_bits = []

        last2bits = [0,0]

        while(True):
            bit =   self.physical_layer.read_signal()
            last2bits = last2bits[1:]+[bit]
            if(last2bits == [1,1]):
                break
        
        len = 0

        for i in range(5):
            bit = self.physical_layer.read_signal()
            len += (2**(i))*bit

        
        for i in range(len):
            bit = self.physical_layer.read_signal()
            recived_bits.append(bit)

        return self.decrypt(recived_bits)
    
    def encrypt(self,data):
        l = len(data)

        final_data = []

        for i in range(5):
            final_data.append(l%2)
            l = int(l/2)
        
        final_data += data
        return final_data

    
    def send_preamble(self):
        self.physical_layer.transmit([0,0,1,1])

    def send_data(self , data):
        self.send_preamble()
        encrypted_data = self.encrypt(data)
        self.physical_layer.transmit(encrypted_data)
    



phy_layer = PhysicalLayer(sample_rate=44100,duration=0.25,f0=400,f1=800,amplitute=1)

dll_layer = DLL(phy_layer)

print(dll_layer.recieve())

#0011 10100 10101
