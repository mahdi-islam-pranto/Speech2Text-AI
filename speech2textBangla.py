# from banglaspeech2text import Speech2Text
# import os
# # Load a model
# models = Speech2Text.list_models() # get a list of available models
# print(models) # print the list of models
# model = models[1] # select a model
# print(model) # print the model name
# model = Speech2Text(model) # load the model


# # Use with file
# # use the file from the computer with a file path
# # Get path to Downloads folder
# downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
# file_name = os.path.join(downloads_path, '245.mp3')  # Replace 'test.wav' with your actual audio filename


# output = model.recognize(file_name)

# print(output) # output will be a dict containing text

# # Write output to text file
# output_text = output
# output_path = os.path.join(downloads_path, 'speech_output_new.txt')

# with open(output_path, 'w', encoding='utf-8') as f:
#     f.write(output_text)

# print(f"Output saved to: {output_path}")


from banglaspeech2text import Speech2Text
import os
from multiprocessing import freeze_support

def main():
    # Load a model
    models = Speech2Text.list_models()  # get a list of available models
    print(models)  # print the list of models
    model = models[1]  # select a model
    print(model)  # print the model name
    model = Speech2Text(model)  # load the model

    # Use with file
    # Get path to Downloads folder
    downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
    file_name = os.path.join(downloads_path, '245.mp3')

    output = model.recognize(file_name)
    print(output)  # output will be a dict containing text

    # Write output to text file
    output_text = output
    output_path = os.path.join(downloads_path, 'speech_output_new.txt')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)

if __name__ == '__main__':
    freeze_support()
    main()