from customtkinter import *
import re
from subprocess import Popen, PIPE
import assembler
from os import remove


class JavaToAssembly:

    def __init__(self):

        set_appearance_mode("dark")
        set_default_color_theme("dark-blue")

        self.app = CTk()
        SCREEN = [1280, 720]
        self.app.geometry(str(SCREEN[0]) + "x" + str(SCREEN[1]))
        self.app.title("Java_To_Assembly.py")

        self.app.columnconfigure("0", weight=5)
        self.app.columnconfigure("1", weight=1)
        self.app.columnconfigure("2", weight=5)
        self.converted = False

        # Creating layout
        javaFrame = CTkFrame(
            master=self.app, width=SCREEN[0]//2, height=SCREEN[1]-100)
        assemblyFrame = CTkFrame(
            master=self.app, width=SCREEN[0]//2, height=SCREEN[1]-100)

        javaFrame.rowconfigure("0", weight=1)
        javaFrame.rowconfigure("1", weight=10)
        javaFrame.rowconfigure("2", weight=1)

        assemblyFrame.rowconfigure("0", weight=1)
        assemblyFrame.rowconfigure("1", weight=7)
        assemblyFrame.rowconfigure("2", weight=1)
        assemblyFrame.rowconfigure("3", weight=2)
        assemblyFrame.rowconfigure("4", weight=1)

        javaLabel = CTkLabel(master=javaFrame, text="Java code goes here:",
                             justify=CENTER)

        self.javaCode = CTkTextbox(
            master=javaFrame, width=(SCREEN[0]//2)-50, height=SCREEN[1]-100)

        assemblyLabel = CTkLabel(master=assemblyFrame, text="Assembly code output:",
                                 justify=CENTER)

        self.assemblyCode = CTkTextbox(
            master=assemblyFrame, width=(SCREEN[0]//2)-50, height=(SCREEN[1]-100)*.7)

        labelOut = CTkLabel(master=assemblyFrame, text="Output displayed here:",
                            justify=CENTER)

        self.assemblyCodeOut = CTkTextbox(
            master=assemblyFrame, width=(SCREEN[0]//2)-50, height=(SCREEN[1]-100)*.25)

        # make assembly textbox readonly
        self.assemblyCode.configure(state="disabled")
        self.assemblyCodeOut.configure(state="disabled")

        self.convertButton = CTkButton(
            javaFrame, text="Convert & Run", command=self.convert)
        self.exportButton = CTkButton(
            assemblyFrame, text="Export", command=self.export)

        # Export is disabled by default
        self.exportButton.configure(state="disabled")

        # placing UI objects using grid system
        javaFrame.grid(row=0, column=0)
        javaLabel.grid(row=0, column=0)
        self.javaCode.grid(row=2, column=0, padx=10)

        assemblyFrame.grid(row=0, column=2)
        assemblyLabel.grid(row=0, column=0)
        self.assemblyCode.grid(row=1, column=0, padx=10)
        labelOut.grid(row=2, column=0)
        self.assemblyCodeOut.grid(row=3, column=0, padx=10)

        self.convertButton.grid(row=4, column=0, pady=10)
        self.exportButton.grid(row=4, column=0, pady=10)

        self.app.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.app.mainloop()

    def convert(self):

        code = self.javaCode.get("0.0", "end").strip()
        javaStatements = code.replace('\t', '')

        # Preserve block statements and multiline comments from split
        comments = re.findall(r"/\*(.+?)\*/", javaStatements, re.DOTALL)
        javaStatements = re.sub(
            r"/\*(.+?)\*/", "/**/", javaStatements, 0, re.DOTALL)

        for comment in comments:
            comment = comment.strip().split('\n')
            comment = ["#" + com + '\n' for com in comment]
            javaStatements = re.sub(
                "/\*\*/", "\n" + "".join(comment), javaStatements, 1, re.DOTALL)

        blocks = re.findall(r"{(.+?)}", javaStatements, re.DOTALL)
        javaStatements = re.sub(
            r"{(.+?)}", "{}\n", javaStatements, 0, re.DOTALL)

        javaStatements = javaStatements.split('\n')

        # Reintegrate block statements and comments
        blockCount = 0
        for i, statement in enumerate(javaStatements):

            if "{}" in statement:
                javaStatements[i] = statement.replace(
                    '{}', "{" + blocks[blockCount].replace('\n', '') + "}")
                blockCount += 1

                # Join the block with its definition(if not already joined)
                if statement.strip()[0] == "{":
                    javaStatements[i-1:i +
                                   1] = [''.join(javaStatements[i-1:i+1])]

        # Remove empty lines and lines that only have whitespaces in them
        javaStatements = [
            i for i in javaStatements if not i.isspace() and i != '']

        # print(javaStatements)
        # TODO: FEED CONVERTER "javaStatements" And then display output on self.assemblyCode with assembly.insert
        try:
            convertedCodeText, convertedCodeData = assembler.handler(
                javaStatements)
            self.assemblyCode.configure(state="normal", text_color="gray90")
            self.assemblyCode.delete("0.0", "end")
            asmCode = '\n'.join(convertedCodeText+convertedCodeData)
            self.assemblyCode.insert("0.0", asmCode)
            self.assemblyCode.configure(state="disabled")
            self.converted = True

            # Display Output of program
            with open("__run.asm", "w") as file:
                file.write(asmCode)

            p = Popen(
                ["java", "-jar", "Mars4_5.jar", "nc", "__run.asm"], stderr=PIPE, stdout=PIPE, universal_newlines=True)

            output, error = p.communicate()

            if "Error in C:\School\Comp Arch\JavaToAssembly\__run.asm" in output:
                return self.error(self.assemblyCodeOut, "", output)

            self.assemblyCodeOut.configure(
                state="normal", text_color="#63ea29")
            self.assemblyCodeOut.delete("0.0", "end")
            self.assemblyCodeOut.insert("0.0", output)
            self.assemblyCodeOut.configure(state="disabled")

            # Enable export functionality
            self.exportButton.configure(state="normal")

        except Exception as e:
            ErrorName = type(e).__name__
            ErrorMessage = e
            return self.error(self.assemblyCode, ErrorMessage, ErrorName)

    def export(self):
        output = self.assemblyCode.get("0.0", "end").strip()

        # Check before export
        if not self.converted or output == "":
            self.error(self.assemblyCode,
                       "Error: can't export an empty script!!")
            return

        # Prompt user for where to save
        saveFile = filedialog.asksaveasfilename(
            title="Save as", filetypes=[("Assembly files", ".asm")], defaultextension=".asm")

        # Save file
        if saveFile:
            with open(saveFile, 'w') as myFile:
                myFile.write(output)

    def error(self, display, msg, error="ERROR"):
        display.configure(state="normal", text_color="#d30e00")
        display.delete("0.0", "end")
        if type(msg) != str:
            msg = msg.__str__()
        display.insert("0.0", error + ':' + msg)
        display.configure(state="disabled")  # text_color="gray90"

    def onClosing(self):
        # print("Dying slowly and painfully")
        try:
            remove('__run.asm')
        except:
            pass
        finally:
            exit()


if __name__ == '__main__':
    JavaToAssembly()
