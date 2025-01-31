import numpy as np
import pandas as pd 
import tkinter as tk
from tkinter import messagebox
import tensorflow as tf
from tensorflow.keras.models import Model 
from tensorflow.keras.layers import Input, LSTM, Dense
from tensorflow.keras.preprocessing.sequence import pad_sequences 
from tensorflow.keras.preprocessing.text import Tokenizer

# Load the data
df = pd.read_csv("Pt.csv")


# Tokenize English and Portuguese
english_tokenizer = Tokenizer()
portuguese_tokenizer = Tokenizer()

english_tokenizer.fit_on_texts("english")
portuguese_tokenizer.fit_on_texts("portuguese")

# Convert to sequences
english_sequences = english_tokenizer.texts_to_sequences("english")
portuguese_sequences = portuguese_tokenizer.texts_to_sequences("portuguese")

# Pad sequences
max_len_english = max(len(seq) for seq in english_sequences)
max_len_portuguese = max(len(seq) for seq in portuguese_sequences)

english_padded = pad_sequences(english_sequences, maxlen=max_len_english, padding="post")
portuguese_padded = pad_sequences(portuguese_sequences, maxlen=max_len_portuguese, padding="post")

latent_dim = 64

# Encoder
encoder_inputs = Input(shape=(max_len_english,))
encoder_embedding = tf.keras.layers.Embedding(len(english_tokenizer.word_index) + 1, latent_dim)(encoder_inputs)
_, state_h, state_c = LSTM(latent_dim, return_state=True)(encoder_embedding)
encoder_states = [state_h, state_c]

# Decoder
decoder_inputs = Input(shape=(max_len_portuguese,))
decoder_embedding = tf.keras.layers.Embedding(len(portuguese_tokenizer.word_index) + 1, latent_dim)(decoder_inputs)
decoder_lstm = LSTM(latent_dim, return_sequences=True, return_state=True)
decoder_outputs, _, _ = decoder_lstm(decoder_embedding, initial_state=encoder_states)
decoder_dense = Dense(len(portuguese_tokenizer.word_index) + 1, activation="softmax")
decoder_outputs = decoder_dense(decoder_outputs)

# Define model
model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
model.compile(optimizer="adam", loss="sparse_categorical_crossentropy")

decoder_target_data = np.expand_dims(portuguese_padded, -1)

model.fit([english_padded, portuguese_padded], decoder_target_data, batch_size=2, epochs=10)

# Translation function
def translate_sentence(input_sentence):
    input_seq = english_tokenizer.texts_to_sequences([input_sentence])
    input_seq = pad_sequences(input_seq, maxlen=max_len_english, padding="post")

    states_value = model.predict([input_seq, np.zeros((1, max_len_portuguese))], verbose=0)
    target_seq = np.zeros((1, 1))
    target_seq[0, 0] = portuguese_tokenizer.word_index.get("<start>", 0)

    translated_sentence = ""
    for _ in range(max_len_portuguese):
        output_tokens, h, c = model.predict([target_seq] + states_value, verbose=0)
        sampled_token_index = np.argmax(output_tokens[0, -1, :])
        sampled_word = portuguese_tokenizer.index_word.get(sampled_token_index, "")

        if sampled_word == "<end>":
            break

        translated_sentence += " " + sampled_word

        target_seq = np.zeros((1, 1))
        target_seq[0, 0] = sampled_token_index

        states_value = [h, c]

    return translated_sentence.strip()

# Create the GUI
def create_gui():
    def on_translate():
        english_text = input_text.get("1.0", tk.END).strip()
        if not english_text:
            messagebox.showerror("Error", "Please enter a sentence to translate.")
            return
        translation = translate_sentence(english_text)
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, translation)

    # Initialize the main window
    window = tk.Tk()
    window.title("Language Translator")
    window.geometry("500x300")

    # Input label and text box
    input_label = tk.Label(window, text="Enter English Sentence:")
    input_label.pack(pady=5)

    input_text = tk.Text(window, height=5, width=50)
    input_text.pack(pady=5)

    # Translate button
    translate_button = tk.Button(window, text="Translate", command=on_translate)
    translate_button.pack(pady=5)

    # Output label and text box
    output_label = tk.Label(window, text="Translated Portuguese Sentence:")
    output_label.pack(pady=5)

    output_text = tk.Text(window, height=5, width=50, state=tk.NORMAL)
    output_text.pack(pady=5)

    # Run the GUI event loop
    window.mainloop()

# Run the GUI
create_gui()
