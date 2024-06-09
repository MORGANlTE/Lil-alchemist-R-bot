# All numbers in this code are close approximations of what they should be, but may not be perfectly accurate
#import tkinter as tk
#from tkinter import messagebox
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageTk
import requests
import os
import discord


def imageeditor(cardname, rarity, level, attack, defense, isFinalForm, offset_x, offset_y, resize_factor_override, imgurl, image_location):
    # Save the image locally
    r = requests.get(imgurl)
    with open(f"{image_location}{cardname}.png", "wb") as f:
        f.write(r.content)

    



    # Load all images to be used
    card_sprite = Image.open(image_location+cardname+".png")
    try:
        borderimage = Image.open(image_location+"Card"+rarity+level+".png")
    except Exception as e:
        #messagebox.showerror("Error", f"An error occurred: {str(e)}")
        borderimage = Image.open(image_location+"Card"+rarity+".png")
    #levelimage = Image.open(rarity+"Level"+level+".png")
    attackbox = Image.open(image_location+"AttackBox.png")
    defensebox = Image.open(image_location+"DefenseBox.png")
    attackbattle = Image.open(image_location+"AttackBattle.png")
    defensebattle = Image.open(image_location+"DefenseBattle.png")
    if isFinalForm == True:
        finalform_orb = Image.open(image_location+"FinalFormIcon.png")
        background_image = Image.open(image_location+"CardBackground"+rarity+".png")
        # decreasing the brightness of the background by 30%
        enhancer = ImageEnhance.Brightness(background_image)
        background_image = enhancer.enhance(0.7)
    elif rarity == "Onyx":
        finalform_orb = Image.open(image_location+"ComboIcon.png")
        background_image = Image.open(image_location+"CardBackground"+rarity+".png")
        # decreasing the brightness of the background by 30%
        enhancer = ImageEnhance.Brightness(background_image)
        background_image = enhancer.enhance(0.7)
    else:
        finalform_orb = Image.open(image_location+"ComboIcon.png")
        background_image = Image.open(image_location+"CardBackgroundCombo.png")

    # Define the coordinates where you want to place the card sprite (from top-left corner)
    # the sprite is first resized to fit into a 700x733 rectangle, then positioned in the center of the rectangle

    borderx = 34
    rect_x = 768 - (2*borderx)
    bordery_top = 155
    bordery_bottom = 136
    rect_y = 1024 - bordery_bottom - bordery_top

    if rect_x/int(card_sprite.width) > rect_y/int(card_sprite.height):
        # tall image
        resize_factor = rect_y/int(card_sprite.height)*resize_factor_override/100
        y = bordery_top
        x = borderx + int(round(((rect_x-(card_sprite.width*resize_factor))/2), 0))
    else:
        # wide image
        resize_factor = rect_x/int(card_sprite.width)*resize_factor_override/100
        y = bordery_top + int(round(((rect_y-(card_sprite.height*resize_factor))/2), 0))
        x = borderx

    card_sprite_position = (x + offset_x, y + offset_y)

    # Resize the images
    card_sprite = card_sprite.resize((int(card_sprite.width * resize_factor), int(card_sprite.height * resize_factor)))
    background_image = background_image.resize((768, 1024))
    borderimage = borderimage.resize((768, 1024))
    #levelimage = levelimage.resize((768, 1024))
    attackbox = attackbox.resize((236, 120))
    defensebox = defensebox.resize((236, 120))
    attackbattle = attackbattle.resize((76, 95)) 
    defensebattle = defensebattle.resize((76, 81)) 
    finalform_orb = finalform_orb.resize((99, 99))

    # Create a composite image with transparency
    # images are layered on top of eachother in the order below
    result = Image.new("RGBA", background_image.size)
    result.paste(background_image, (0, 0))
    result.alpha_composite(card_sprite.convert("RGBA"), card_sprite_position)
    result.alpha_composite(borderimage.convert("RGBA"), (0, 0))
    #result.alpha_composite(levelimage.convert("RGBA"), (0, 0))
    result.alpha_composite(attackbox.convert("RGBA"), (235, 53))
    result.alpha_composite(defensebox.convert("RGBA"), (480, 53))
    result.alpha_composite(attackbattle.convert("RGBA"), (243, 66))
    result.alpha_composite(defensebattle.convert("RGBA"), (492, 74))
    result.alpha_composite(finalform_orb.convert("RGBA"), (11, 167))

    # Create a drawing object
    draw = ImageDraw.Draw(result)

    # Specify the font and size
    assert os.path.isfile(image_location+"GrilledCheeseBTNCnBold.TTF"), "Font file is missing:" + image_location+"GrilledCheeseBTNCnBold.TTF"
    font = ImageFont.truetype(image_location+"GrilledCheeseBTNCnBold.TTF", size=100)

    # Adding text
    text_width = draw.textlength(cardname.replace("_", " "), font)
    for char in cardname.replace("_", " "):
        text_width -= 3
    text_position = ((result.width - text_width) // 2, 904)

    if rarity == "Onyx":
        color = (205,255,255,255) #light blue
    else:
        color = (0, 0, 0, 255) #white

    for char in cardname.replace("_", " "):
        draw.text(text_position, char, font=font, fill=color)
        text_position = (text_position[0] + font.getbbox(char)[2] - 3, text_position[1])

    attack_text_width = draw.textlength(attack, font)
    attack_text_position = (((471-311-attack_text_width)/2)+311+2, 59)
    draw.text(attack_text_position, attack, font=font, fill=(255, 255, 255, 255))

    defense_text_width = draw.textlength(defense, font)
    defense_text_position = (((712-556-defense_text_width)/2)+556+4, 59)
    draw.text(defense_text_position, defense, font=font, fill=(255, 255, 255, 255))

    # Resizing
    # This is due to the images being rendered to 270,360 on the wiki anyways so uploading a larger image is unneeded
    #result = result.resize((270,360))

    # Close all the images
    background_image.close()
    card_sprite.close()
    borderimage.close()
    attackbox.close()
    defensebox.close()
    attackbattle.close()
    defensebattle.close()
    finalform_orb.close()

    # Save the resulting image
    result.save(f"{image_location}{cardname}{rarity}{attack}{defense}.png")

    # Return the resulting image to be used by other functions
    fileM = discord.File(
            f"{image_location}{cardname}{rarity}{attack}{defense}.png",
            filename=f"{image_location}{cardname}{rarity}{attack}{defense}.png"
        )

    # remove original image:
    os.remove(f"{image_location}{cardname}.png")
    
    return(fileM)




# class CardImageGeneratorUI:
#     def __init__(self, master):
#         self.master = master
#         master.title("Card Image Generator")

#         self.create_widgets()

#     def create_widgets(self):
#         tk.Label(self.master, text="Card Name:").grid(row=0, column=0)
#         self.cardname_entry = tk.Entry(self.master)
#         self.cardname_entry.grid(row=0, column=1)

#         tk.Label(self.master, text="Card Rarity:").grid(row=1, column=0)
#         self.rarity_var = tk.StringVar(self.master)
#         self.rarity_var.set("Bronze")  # Set default value
#         self.rarity_options = ["Bronze", "Silver", "Gold", "Diamond", "Onyx"]
#         self.rarity_dropdown = tk.OptionMenu(self.master, self.rarity_var, *self.rarity_options)
#         self.rarity_dropdown.grid(row=1, column=1)

#         tk.Label(self.master, text="Card Level:").grid(row=2, column=0)
#         self.level_entry = tk.Entry(self.master)
#         self.level_entry.grid(row=2, column=1)

#         tk.Label(self.master, text="Attack:").grid(row=3, column=0)
#         self.attack_entry = tk.Entry(self.master)
#         self.attack_entry.grid(row=3, column=1)

#         tk.Label(self.master, text="Defense:").grid(row=4, column=0)
#         self.defense_entry = tk.Entry(self.master)
#         self.defense_entry.grid(row=4, column=1)

#         tk.Label(self.master, text="Offset X:").grid(row=5, column=0)
#         self.offset_x_entry = tk.Entry(self.master)
#         self.offset_x_entry.grid(row=5, column=1)

#         tk.Label(self.master, text="Offset Y:").grid(row=6, column=0)
#         self.offset_y_entry = tk.Entry(self.master)
#         self.offset_y_entry.grid(row=6, column=1)

#         tk.Label(self.master, text="Resize factor (%):").grid(row=7, column=0)
#         self.resize_factor_entry = tk.Entry(self.master)
#         self.resize_factor_entry.grid(row=7, column=1)

#         self.final_form_var = tk.BooleanVar()
#         self.final_form_checkbox = tk.Checkbutton(self.master, text="Final Form", variable=self.final_form_var)
#         self.final_form_checkbox.grid(row=8, columnspan=2)

#         self.start_button = tk.Button(self.master, text="PREVIEW", command=self.start_processing)
#         self.start_button.grid(row=9, column=0, pady=10)

#         self.save_button = tk.Button(self.master, text="SAVE", command=self.save_image)
#         self.save_button.grid(row=9, column=1, pady=10)

#         # Label to display the generated image
#         self.image_label = tk.Label(self.master)
#         self.image_label.grid(row=10, columnspan=2)

#         # Placeholder for the generated image
#         self.generated_image = None

#     def start_processing(self):
#         cardname = self.cardname_entry.get()
#         rarity = self.rarity_var.get()
#         level = self.level_entry.get()
#         attack = self.attack_entry.get()
#         defense = self.defense_entry.get()
#         isFinalForm = self.final_form_var.get()
#         offset_x = self.offset_x_entry.get()
#         offset_y = self.offset_y_entry.get()
#         resize_factor_override = self.resize_factor_entry.get()

#         if not offset_x:
#             offset_x = 0
#         if not offset_y:
#             offset_y = 0
#         if not resize_factor_override:
#             resize_factor_override = 100

#         try:
#             # Get the generated image from the imageeditor function
#             self.generated_image = imageeditor(cardname, rarity, level, attack, defense, isFinalForm, int(offset_x), int(offset_y), int(resize_factor_override))
            
#             # Resize the image to 384x512 px
#             resized_image = self.generated_image.resize((384, 512))
        
#             # Display the generated image on the screen
#             self.display_image(resized_image)
#             messagebox.showinfo("Success", "Image generated successfully!")
#         except Exception as e:
#             messagebox.showerror("Error", f"An error occurred: {str(e)}")

#     def display_image(self, image):
#         # Convert the PIL Image to Tkinter PhotoImage
#         photo_image = ImageTk.PhotoImage(image)
#         self.image_label.configure(image=photo_image)
#         self.image_label.image = photo_image  # Keep a reference to prevent garbage collection

#     def save_image(self):
#         # re-imports the values, in case they were altered, then regenerates the image
#         cardname = self.cardname_entry.get()
#         rarity = self.rarity_var.get().capitalize()
#         level = self.level_entry.get()
#         attack = self.attack_entry.get()
#         defense = self.defense_entry.get()
#         isFinalForm = self.final_form_var.get()
#         offset_x = self.offset_x_entry.get()
#         offset_y = self.offset_y_entry.get()
#         resize_factor_override = self.resize_factor_entry.get()

#         if not offset_x:
#             offset_x = 0
#         if not offset_y:
#             offset_y = 0
#         if not resize_factor_override:
#             resize_factor_override = 100

#         try:
#             self.generated_image = imageeditor(cardname, rarity, level, attack, defense, isFinalForm, int(offset_x), int(offset_y), int(resize_factor_override))
#         except Exception as e:
#             messagebox.showerror("Error", f"An error occurred: {str(e)}")

#         if self.generated_image:
#             # Save file
#             save_name = cardname+rarity+level+attack+defense+".png"
#             self.generated_image.save(save_name)
#             messagebox.showinfo("Success", f"Image saved successfully as {save_name}.png.")
#         else:
#             messagebox.showwarning("Warning", "No image has been generated yet.")





# def start_UI():
#     root = tk.Tk()
#     app = CardImageGeneratorUI(root)
#     root.mainloop()





#if __name__ == "__main__":
#    start_UI()